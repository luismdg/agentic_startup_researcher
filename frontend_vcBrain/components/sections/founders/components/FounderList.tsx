import type { Founder } from "@/lib/types";
import { Table, THead, TBody, TRow, TH, TD } from "@/components/ui/Table/Table";
import ScoreBar from "@/components/ui/ScoreBar/ScoreBar";
import TrendArrow from "@/components/ui/TrendArrow/TrendArrow";
import Badge from "@/components/ui/Badge/Badge";
import Monogram from "./Monogram";
import styles from "./FounderList.module.css";

interface FounderListProps {
  founders: Founder[];
  selectedId: string;
  onSelect: (id: string) => void;
}

export default function FounderList({ founders, selectedId, onSelect }: FounderListProps) {
  if (founders.length === 0) {
    return <p className={styles.empty}>No founders match the current filters.</p>;
  }

  return (
    <Table>
      <THead>
        <tr>
          <TH>#</TH>
          <TH>Founder</TH>
          <TH align="right">Score</TH>
          <TH>Trend</TH>
        </tr>
      </THead>
      <TBody>
        {founders.map((f, i) => (
          <TRow key={f.id} onClick={() => onSelect(f.id)} active={f.id === selectedId}>
            <TD>
              <span className={styles.rank}>{i + 1}</span>
            </TD>
            <TD>
              <div className={styles.identity}>
                <Monogram initials={f.initials} size="sm" />
                <div className={styles.identityText}>
                  <div className={styles.nameRow}>
                    <span className={styles.name}>{f.name}</span>
                    {f.firstTimeFounder && <Badge variant="info">First-time</Badge>}
                  </div>
                  <div className={styles.archetype}>{f.archetype}</div>
                </div>
              </div>
            </TD>
            <TD align="right">
              <ScoreBar score={f.founderScore} />
            </TD>
            <TD>
              <TrendArrow trend={f.founderScoreTrend} label={false} />
            </TD>
          </TRow>
        ))}
      </TBody>
    </Table>
  );
}
