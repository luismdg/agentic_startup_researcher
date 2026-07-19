"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { Startup } from "@/lib/types";
import Input from "@/components/ui/Input/Input";
import StatusBadge from "@/components/ui/StatusBadge/StatusBadge";
import Icon from "@/components/ui/Icon/Icon";
import { Table, THead, TBody, TRow, TH, TD } from "@/components/ui/Table/Table";
import styles from "./OpportunityGate.module.css";

interface OpportunityGateProps {
  startups: Startup[];
  basePath: string;
  title?: string;
  description?: string;
}

export default function OpportunityGate({
  startups,
  basePath,
  title = "Pick a startup to look at",
  description = "Type a name or word, or just browse the list — then click one to open it. Nothing shows until you pick.",
}: OpportunityGateProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return startups;
    return startups.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.sector.toLowerCase().includes(q) ||
        s.geography.toLowerCase().includes(q) ||
        s.tags.some((t) => t.toLowerCase().includes(q))
    );
  }, [startups, query]);

  return (
    <div className={styles.gate}>
      <div className={styles.header}>
        <span className={styles.eyebrow}>
          <Icon name="search" size={14} /> Let&rsquo;s find what you want
        </span>
        <h2 className={styles.title}>{title}</h2>
        <p className={styles.description}>{description}</p>
      </div>
      <Input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Type a name, industry, place, or keyword…"
        aria-label="Search startups"
        className={styles.search}
      />
      {filtered.length === 0 ? (
        <p className={styles.empty}>Nothing matches &ldquo;{query}&rdquo; — try a different word.</p>
      ) : (
        <Table>
          <THead>
            <tr>
              <TH>Startup</TH>
              <TH>Industry & Stage</TH>
              <TH>Where it&rsquo;s at</TH>
              <TH align="right">Fit</TH>
            </tr>
          </THead>
          <TBody>
            {filtered.map((s) => (
              <TRow key={s.id} onClick={() => router.push(`${basePath}?startup=${s.id}`)}>
                <TD>
                  <div className={styles.name}>{s.name}</div>
                  <div className={styles.tagline}>{s.tagline}</div>
                </TD>
                <TD>
                  <div>{s.sector}</div>
                  <div className={styles.stage}>{s.stage}</div>
                </TD>
                <TD>
                  <StatusBadge status={s.status} />
                </TD>
                <TD align="right">{s.thesisFitScore}</TD>
              </TRow>
            ))}
          </TBody>
        </Table>
      )}
    </div>
  );
}
