import type { SwotContent } from "@/lib/types";
import styles from "./SwotGrid.module.css";

const QUADRANTS: { key: keyof SwotContent; label: string }[] = [
  { key: "strengths", label: "Strengths" },
  { key: "weaknesses", label: "Weaknesses" },
  { key: "opportunities", label: "Opportunities" },
  { key: "threats", label: "Threats" },
];

/** 2x2 SWOT grid, quadrants separated by thin dividers (not boxed cards). */
export default function SwotGrid({ swot }: { swot: SwotContent }) {
  return (
    <div className={styles.grid}>
      {QUADRANTS.map((quadrant) => (
        <div className={styles.quadrant} key={quadrant.key}>
          <h3 className={styles.quadrantTitle}>{quadrant.label}</h3>
          <ul className={styles.list}>
            {swot[quadrant.key].map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
