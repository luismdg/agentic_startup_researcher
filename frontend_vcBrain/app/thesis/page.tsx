import PageHeader from "@/components/layout/PageHeader/PageHeader";
import ThesisView from "@/components/sections/thesis/components/ThesisView";
import { thesis } from "@/lib/data";

export default function ThesisPage() {
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
      />
    </>
  );
}
