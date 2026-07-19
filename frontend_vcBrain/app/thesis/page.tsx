import PageHeader from "@/components/layout/PageHeader/PageHeader";
import ThesisView from "@/components/sections/thesis/components/ThesisView";
import { thesis, startups } from "@/lib/data";
import { fetchLiveStartups } from "@/lib/liveApi";

export const dynamic = "force-dynamic";

export default async function ThesisPage() {
  const liveStartups = await fetchLiveStartups();
  const allStartups = [...liveStartups, ...startups.filter((s) => !liveStartups.some((l) => l.id === s.id))];
  const investedStartups = allStartups.filter((s) => s.status === "invested");

  return (
    <>
      <PageHeader
        title="My Focus"
        description="This is where you tell VC Brain what you're actually looking for. Pick a starting point, tweak it your way, or just type it in your own words below."
      />
      <ThesisView
        presets={thesis.presets}
        activePresetId={thesis.activePresetId}
        autoMapExamples={thesis.autoMapExamples}
        investedStartups={investedStartups}
      />
    </>
  );
}
