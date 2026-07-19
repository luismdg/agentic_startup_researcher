import { redirect } from "next/navigation";

interface DiligenceRedirectProps {
  searchParams: Promise<{ startup?: string }>;
}

// Checklist merged into /evaluate?tab=checklist -- see app/evaluate/page.tsx.
export default async function DiligenceRedirect({ searchParams }: DiligenceRedirectProps) {
  const { startup } = await searchParams;
  redirect(startup ? `/evaluate?tab=checklist&startup=${startup}` : "/evaluate");
}
