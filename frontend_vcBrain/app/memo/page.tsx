import { redirect } from "next/navigation";

interface MemoRedirectProps {
  searchParams: Promise<{ startup?: string }>;
}

// Report merged into /evaluate?tab=report -- see app/evaluate/page.tsx.
export default async function MemoRedirect({ searchParams }: MemoRedirectProps) {
  const { startup } = await searchParams;
  redirect(startup ? `/evaluate?tab=report&startup=${startup}` : "/evaluate");
}
