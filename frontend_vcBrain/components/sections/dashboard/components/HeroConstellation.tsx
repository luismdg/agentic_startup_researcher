"use client";

import dynamic from "next/dynamic";
import type { CSSProperties } from "react";
import type { Startup, Screening } from "@/lib/types";
import TrendArrow from "@/components/ui/TrendArrow/TrendArrow";
import CountUp from "@/components/ui/CountUp/CountUp";
import TiltCard from "@/components/ui/TiltCard/TiltCard";
import styles from "./HeroConstellation.module.css";

// react-three-fiber creates a WebGL context on mount; it must never run
// during SSR, so the whole 3D scene is loaded client-only.
const AxisConstellation = dynamic(() => import("@/components/three/AxisConstellation"), {
  ssr: false,
  loading: () => <div className={styles.canvasFallback} aria-hidden="true" />,
});

interface HeroConstellationProps {
  startups: Startup[];
  featured?: { startup: Startup; screening: Screening };
}

export default function HeroConstellation({ startups, featured }: HeroConstellationProps) {
  const total = startups.length;
  const avgFit = Math.round(startups.reduce((a, s) => a + s.thesisFitScore, 0) / (total || 1));
  const trendingUp = startups.filter((s) => s.momentumTrend === "up").length;

  return (
    <section className={styles.hero}>
      <div className={styles.aurora} aria-hidden="true" />
      <TiltCard className={styles.panel} maxTilt={4}>
        <div className={styles.copy}>
          <span className={styles.eyebrow}>Live thesis lens · Northstar Seed Fund</span>
          <h1 className={styles.title}>
            Three signals.
            <br />
            Never one number.
          </h1>
          <p className={styles.subtitle}>
            Founder, Market, and Idea-fit are scored independently for every startup you track —
            and they stay that way all the way to the ranked list below. Nothing here is an
            average pretending to be an insight.
          </p>

          <div className={styles.stats}>
            <div className={styles.stat}>
              <span className={styles.statValue}>
                <CountUp value={total} />
              </span>
              <span className={styles.statLabel}>Tracked opportunities</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statValue}>
                <CountUp value={avgFit} />
              </span>
              <span className={styles.statLabel}>Avg. thesis fit</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statValue}>
                <CountUp value={trendingUp} />/{total}
              </span>
              <span className={styles.statLabel}>Trending up</span>
            </div>
          </div>

          {featured && (
            <div className={styles.legend}>
              <span className={styles.legendCaption}>Featured this session — {featured.startup.name}</span>
              <div className={styles.legendRow}>
                <span
                  className={styles.legendChip}
                  style={{ "--dot": "var(--cosmic-founder)" } as CSSProperties}
                >
                  <span className={styles.dot} />
                  Founder {featured.screening.founder.score}
                  <TrendArrow trend={featured.screening.founder.trend} label={false} />
                </span>
                <span
                  className={styles.legendChip}
                  style={{ "--dot": "var(--cosmic-market)" } as CSSProperties}
                >
                  <span className={styles.dot} />
                  Market {featured.screening.market.score}
                  <TrendArrow trend={featured.screening.market.trend} label={false} />
                </span>
                <span
                  className={styles.legendChip}
                  style={{ "--dot": "var(--cosmic-idea)" } as CSSProperties}
                >
                  <span className={styles.dot} />
                  Idea fit {featured.screening.ideaMarketFit.score}
                  <TrendArrow trend={featured.screening.ideaMarketFit.trend} label={false} />
                </span>
              </div>
            </div>
          )}
        </div>

        <div className={styles.canvasWrap}>
          <AxisConstellation
            founder={{
              score: featured?.screening.founder.score ?? 60,
              trend: featured?.screening.founder.trend ?? "flat",
            }}
            market={{
              score: featured?.screening.market.score ?? 60,
              trend: featured?.screening.market.trend ?? "flat",
            }}
            idea={{
              score: featured?.screening.ideaMarketFit.score ?? 60,
              trend: featured?.screening.ideaMarketFit.trend ?? "flat",
            }}
            height={420}
          />
        </div>
      </TiltCard>
    </section>
  );
}