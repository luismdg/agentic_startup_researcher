import styles from "./EmptyValue.module.css";
import type { FieldAvailability } from "@/lib/types";

const COPY: Record<Exclude<FieldAvailability, "available">, string> = {
  not_disclosed: "Not disclosed",
  unavailable_at_this_stage: "Unavailable at this stage",
};

export default function EmptyValue({ reason }: { reason: Exclude<FieldAvailability, "available"> }) {
  return <span className={styles.empty}>{COPY[reason]}</span>;
}
