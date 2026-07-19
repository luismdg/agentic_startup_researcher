import { redirect } from "next/navigation";

// Founders merged into Discover's "Founders" tab -- see app/sourcing/page.tsx.
export default function FoundersRedirect() {
  redirect("/sourcing");
}
