"""
Thin wrapper that turns a (system, user) message pair into a validated
Pydantic object, using each provider's structured-output primitive so we get
a schema-conformant object back directly instead of parsing JSON out of a
free-text blob.

Provider is chosen via LLM_PROVIDER=anthropic|openai|fake (default:
anthropic). scorer_service.py / memo_service.py only ever call
call_structured() -- they never know which provider is behind it, so
swapping providers is a one-line env var change, not a code change anywhere
else.

- anthropic: forces a tool call whose input_schema is the Pydantic model's
  JSON schema (Claude's structured-output primitive).
- openai: uses the SDK's built-in Pydantic parsing (response_format=<model>
  on client.beta.chat.completions.parse), OpenAI's equivalent primitive.
  Requires a model that supports it (gpt-4o-2024-08-06+, gpt-4o-mini, etc).
  Unlike Anthropic, OpenAI puts the system prompt inside the same messages
  list (role="system"), which is exactly the shape build_scorer_messages()/
  build_memo_messages() already produce -- no reshaping needed here.
- fake: no network call, no API key, $0 cost. Returns canned-but-schema-valid
  data from fake_llm_fixtures.py so the whole pipeline (dashboard, scoring,
  memo rendering, trust bar) can be exercised before spending real credit.

One retry on validation failure/refusal for either provider: a single fresh
retry catches transient misses without masking a systematically broken
prompt -- if it fails twice, that's a prompt/schema bug worth surfacing, not
something to keep retrying silently.

RELAX_TLS_STRICT_X509 (opt-in, off by default): some machines run software
(corporate proxies, or AV "HTTPS scanning" like Norton's Web/Mail Shield)
that intercepts TLS by re-signing traffic with a locally-installed root
certificate. Python 3.13 turned on OpenSSL's strict X.509 conformance
checking by default, which rejects some of those locally-generated
certificates even though the OS itself trusts them -- connections fail with
"Basic Constraints of CA cert not marked critical" before any request
reaches the provider. Setting RELAX_TLS_STRICT_X509=1 clears just that one
strict-conformance flag (hostname and chain-of-trust verification stay on)
so requests can get through on an affected machine. Leave unset unless you
hit exactly that error -- it's a local-environment workaround, not something
this project should weaken by default for everyone else.
"""

from __future__ import annotations

import os
import ssl
from typing import Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic").lower()

_DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-5",
    "openai": "gpt-4o-2024-08-06",
}
MODEL = os.environ.get("REASONING_ENGINE_MODEL", _DEFAULT_MODELS.get(PROVIDER, "claude-sonnet-5"))
MAX_TOKENS = int(os.environ.get("REASONING_ENGINE_MAX_TOKENS", "4096"))
_RELAX_TLS_STRICT_X509 = os.environ.get("RELAX_TLS_STRICT_X509") == "1"

_anthropic_client = None
_openai_client = None
_relaxed_http_client = None


class StructuredCallError(RuntimeError):
    pass


def _get_relaxed_http_client():
    """httpx.Client with strict X.509 conformance checking disabled -- see
    RELAX_TLS_STRICT_X509 in the module docstring. Verification stays on."""
    global _relaxed_http_client
    if _relaxed_http_client is None:
        import certifi
        import httpx

        ctx = ssl.create_default_context(cafile=certifi.where())
        if hasattr(ssl, "VERIFY_X509_STRICT"):
            ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        _relaxed_http_client = httpx.Client(verify=ctx)
    return _relaxed_http_client


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic  # imported lazily so an openai-only install doesn't need this package
        kwargs = {"api_key": os.environ["ANTHROPIC_API_KEY"]}
        if _RELAX_TLS_STRICT_X509:
            kwargs["http_client"] = _get_relaxed_http_client()
        _anthropic_client = anthropic.Anthropic(**kwargs)
    return _anthropic_client


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        import openai  # imported lazily so an anthropic-only install doesn't need this package
        kwargs = {"api_key": os.environ["OPENAI_API_KEY"]}
        if _RELAX_TLS_STRICT_X509:
            kwargs["http_client"] = _get_relaxed_http_client()
        _openai_client = openai.OpenAI(**kwargs)
    return _openai_client


def _call_anthropic(messages: List[Dict[str, str]], response_model: Type[T]) -> T:
    system_prompt = next(m["content"] for m in messages if m["role"] == "system")
    user_messages = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]

    tool_name = f"emit_{response_model.__name__.lower()}"
    response = _get_anthropic_client().messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        tools=[{
            "name": tool_name,
            "description": f"Emit the {response_model.__name__} result. Must be called exactly once.",
            "input_schema": response_model.model_json_schema(),
        }],
        tool_choice={"type": "tool", "name": tool_name},
        messages=user_messages,
    )

    tool_use = next((b for b in response.content if b.type == "tool_use" and b.name == tool_name), None)
    if tool_use is None:
        raise StructuredCallError(f"model did not call {tool_name}")
    return response_model.model_validate(tool_use.input)


def _call_fake(messages: List[Dict[str, str]], response_model: Type[T]) -> T:
    from app.services.fake_llm_fixtures import FAKE_BUILDERS

    builder = FAKE_BUILDERS.get(response_model.__name__)
    if builder is None:
        raise StructuredCallError(f"no fake fixture registered for {response_model.__name__}")
    return response_model.model_validate(builder())


def _call_openai(messages: List[Dict[str, str]], response_model: Type[T]) -> T:
    completion = _get_openai_client().beta.chat.completions.parse(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=messages,
        response_format=response_model,
    )
    choice = completion.choices[0]
    if choice.message.refusal:
        raise StructuredCallError(f"model refused: {choice.message.refusal}")
    if choice.message.parsed is None:
        raise StructuredCallError("model returned no parsed output")
    return choice.message.parsed


_CALLERS = {"anthropic": _call_anthropic, "openai": _call_openai, "fake": _call_fake}


def call_structured(messages: List[Dict[str, str]], response_model: Type[T], attempts: int = 2) -> T:
    if PROVIDER not in _CALLERS:
        raise StructuredCallError(f"unknown LLM_PROVIDER '{PROVIDER}', expected one of {list(_CALLERS)}")
    caller = _CALLERS[PROVIDER]

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return caller(messages, response_model)
        except (ValidationError, StructuredCallError) as e:
            last_error = e
            continue

    raise StructuredCallError(
        f"failed to get a valid {response_model.__name__} via {PROVIDER} after {attempts} attempt(s): {last_error}"
    )
