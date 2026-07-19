import { redirect } from "next/navigation";

interface DecisionRedirectProps {
  searchParams: Promise<{ startup?: string }>;
}

// Decision merged into /evaluate?tab=decision -- see app/evaluate/page.tsx.
export default async function DecisionRedirect({ searchParams }: DecisionRedirectProps) {
  const { startup } = await searchParams;
  redirect(startup ? `/evaluate?tab=decision&startup=${startup}` : "/evaluate");
}
