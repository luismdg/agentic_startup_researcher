import type { Memo } from "@/lib/types";
import Icon from "@/components/ui/Icon/Icon";
import styles from "./AdversarialView.module.css";

interface AdversarialViewProps {
  adversarialView: Memo["decision"]["adversarialView"];
}

export default function AdversarialView({ adversarialView }: AdversarialViewProps) {
  return (
    <div className={styles.wrapper}>
      <h2 className={styles.heading}>
        <Icon name="counter" size={18} /> The Case Against It
      </h2>
      <p className={styles.subheading}>Playing devil&rsquo;s advocate on purpose — kept separate from our actual call above.</p>

      <div className={styles.counterThesis}>
        <span className={styles.label}>Why this might not work</span>
        <p className={styles.counterText}>{adversarialView.counterThesis}</p>
      </div>

      <div className={styles.block}>
        <span className={styles.label}>The biggest risks</span>
        <ul className={styles.risksList}>
          {adversarialView.keyRisks.map((risk, i) => (
            <li key={`${i}-${risk}`} className={styles.riskItem}>
              {risk}
            </li>
          ))}
        </ul>
      </div>

      <div className={styles.block}>
        <span className={styles.label}>What would change our mind</span>
        <p className={styles.text}>{adversarialView.whatWouldChangeOurMind}</p>
      </div>
    </div>
  );
}
