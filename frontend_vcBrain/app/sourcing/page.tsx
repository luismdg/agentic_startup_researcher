import PageHeader from "@/components/layout/PageHeader/PageHeader";
import SourcingView from "@/components/sections/sourcing/components/SourcingView";
import { sourcingFeed, sourcingChannels } from "@/lib/data";

export default function SourcingPage() {
  return (
    <>
      <PageHeader
        title="Discover"
        description="New startups, in one place — the ones that applied to you, and the ones we found for you on GitHub, Google, and beyond."
      />
      <SourcingView feed={sourcingFeed} channels={sourcingChannels} />
    </>
  );
}
