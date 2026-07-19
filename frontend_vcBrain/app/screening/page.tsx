import { redirect } from "next/navigation";

interface ScreeningRedirectProps {
  searchParams: Promise<{ startup?: string }>;
}

// Scorecard merged into /evaluate?tab=scorecard -- see app/evaluate/page.tsx.
export default async function ScreeningRedirect({ searchParams }: ScreeningRedirectProps) {
  const { startup } = await searchParams;
  redirect(startup ? `/evaluate?tab=scorecard&startup=${startup}` : "/evaluate");
}
