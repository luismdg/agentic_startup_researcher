"use client";

import { useRouter } from "next/navigation";
import type { Screening, Startup } from "@/lib/types";
import { getFoundersForStartup, getScreening, formatCurrency, formatDate } from "@/lib/data";
import { Table, THead, TBody, TRow, TH, TD } from "@/components/ui/Table/Table";
import ScoreBar from "@/components/ui/ScoreBar/ScoreBar";
import StatusBadge from "@/components/ui/StatusBadge/StatusBadge";
import AxisSnapshot from "./AxisSnapshot";
import MomentumCell from "./MomentumCell";
import styles from "./RankedList.module.css";

interface RankedListProps {
  startups: Startup[];
  // Screenings for live-sourced startups (see lib/liveApi.ts) that
  // getScreening() -- static-mock-only -- can't resolve on its own.
  // Fetched server-side once in app/page.tsx and threaded down, rather than
  // relying on shared mutable state that a concurrent request could clobber.
  liveScreenings?: Record<string, Screening>;
}

export default function RankedList({ startups, liveScreenings = {} }: RankedListProps) {
  const router = useRouter();
  const ranked = [...startups].sort((a, b) => b.thesisFitScore - a.thesisFitScore);

  if (ranked.length === 0) {
    return <p className={styles.empty}>No opportunities match the current filters.</p>;
  }

  return (
    <Table>
      <THead>
        <tr>
          <TH>#</TH>
          <TH>Opportunity</TH>
          <TH>Sector / Stage</TH>
          <TH>Status</TH>
          <TH align="right">Fit with your focus</TH>
          <TH>People / Market / Idea</TH>
          <TH>Momentum</TH>
          <TH align="right">Ask</TH>
          <TH>Last activity</TH>
        </tr>
      </THead>
      <TBody>
        {ranked.map((s, i) => {
          const founders = getFoundersForStartup(s);
          const screening = getScreening(s.id) ?? liveScreenings[s.id];
          return (
            <TRow key={s.id} onClick={() => router.push(`/screening?startup=${s.id}`)}>
              <TD>
                <span className={styles.rank}>{i + 1}</span>
              </TD>
              <TD>
                <div className={styles.name}>{s.name}</div>
                <div className={styles.founders}>
                  {founders.map((f) => f.name).join(" & ")}
                </div>
              </TD>
              <TD>
                <div className={styles.sector}>{s.sector}</div>
                <div className={styles.stage}>{s.stage}</div>
              </TD>
              <TD>
                <StatusBadge status={s.status} />
              </TD>
              <TD align="right">
                <ScoreBar score={s.thesisFitScore} />
              </TD>
              <TD>
                <AxisSnapshot screening={screening} />
              </TD>
              <TD>
                <MomentumCell history={s.momentumHistory} trend={s.momentumTrend} />
              </TD>
              <TD align="right">{formatCurrency(s.askAmount)}</TD>
              <TD>{formatDate(s.lastActivityDate)}</TD>
            </TRow>
          );
        })}
      </TBody>
    </Table>
  );
}
