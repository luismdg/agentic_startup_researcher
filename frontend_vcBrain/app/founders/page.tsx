import PageHeader from "@/components/layout/PageHeader/PageHeader";
import FoundersView from "@/components/sections/founders/components/FoundersView";
import { founders } from "@/lib/data";

export default async function FoundersPage({
  searchParams,
}: {
  searchParams: Promise<{ founder?: string }>;
}) {
  const params = await searchParams;

  return (
    <>
      <PageHeader
        title="Founders"
        description="A score for the person, not just the company — so a great founder still stands out even if their current startup doesn't work out."
      />
      <FoundersView founders={founders} selectedId={params.founder} />
    </>
  );
}
