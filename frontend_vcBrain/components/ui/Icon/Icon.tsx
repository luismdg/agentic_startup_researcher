const PATHS: Record<string, React.ReactNode> = {
  // Overview — asymmetric bento grid
  grid: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="4" rx="1.5" />
      <rect x="14" y="10" width="7" height="11" rx="1.5" />
      <rect x="3" y="13" width="7" height="8" rx="1.5" />
    </>
  ),
  // My Focus — diamond with a center point
  focus: (
    <>
      <path d="M12 3 21 12 12 21 3 12Z" />
      <circle cx="12" cy="12" r="1.8" fill="currentColor" stroke="none" />
    </>
  ),
  // Discover — off-axis orbit
  discover: (
    <>
      <circle cx="12" cy="12" r="8" />
      <ellipse cx="12" cy="12" rx="8" ry="3" transform="rotate(45 12 12)" />
    </>
  ),
  // Founders — two linked people, abstracted as overlapping circles
  founders: (
    <>
      <circle cx="9" cy="9" r="4" />
      <circle cx="16" cy="14.5" r="5" />
    </>
  ),
  // Scorecard — three independent bars, deliberately uneven
  scorecard: (
    <>
      <path d="M4 20v-6" />
      <path d="M11 20V8" />
      <path d="M18 20V4" />
    </>
  ),
  // Fact Check — shield with a checkmark
  factcheck: (
    <>
      <path d="M12 3 20 7v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7Z" />
      <path d="M9 12l2 2 4-4" />
    </>
  ),
  // Checklist — ticks against lines
  checklist: (
    <>
      <path d="M4 6l1.5 1.5L8 4" />
      <path d="M11.5 6H20" />
      <path d="M4 12l1.5 1.5L8 10" />
      <path d="M11.5 12H20" />
      <path d="M4 18l1.5 1.5L8 16" />
      <path d="M11.5 18H20" />
    </>
  ),
  // Report — document with a folded corner
  report: (
    <>
      <path d="M6 3h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
      <path d="M15 3v5h5" />
      <path d="M8 12.5h8" />
      <path d="M8 16.5h5" />
    </>
  ),
  // Decision — a fork in the path
  decision: (
    <>
      <circle cx="12" cy="4" r="1.5" fill="currentColor" stroke="none" />
      <path d="M12 5.5v4.5" />
      <path d="M12 10 6 16.5" />
      <path d="M12 10l6 6.5" />
      <circle cx="6" cy="18.5" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="18" cy="18.5" r="1.5" fill="currentColor" stroke="none" />
    </>
  ),
  // Search — hexagonal lens
  search: (
    <>
      <path d="M6.5 4.5h6.5L16.5 10l-3.5 5.5H6.5L3 10Z" />
      <path d="M15.5 15.5l5 5" />
    </>
  ),
  // Empty tray — nothing here yet
  tray: (
    <>
      <path d="M4 13l3-8h10l3 8" />
      <path d="M4 13v6a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-6" />
      <path d="M4 13h5l1 2h4l1-2h5" />
    </>
  ),
  // Confused — tilted question mark
  confused: (
    <>
      <rect x="4" y="4" width="16" height="16" rx="4" transform="rotate(-4 12 12)" />
      <path d="M9.6 9.3a2.5 2.5 0 1 1 4 2c-.9.6-1.6 1.1-1.6 2.3" />
      <circle cx="12" cy="16.6" r=".9" fill="currentColor" stroke="none" />
    </>
  ),
  // Archive — open folder
  archive: <path d="M3 7a1 1 0 0 1 1-1h5l2 2h9a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1Z" />,
  // Note — document with a pencil stroke
  note: (
    <>
      <path d="M6 3h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
      <path d="M15 3v5h5" />
      <path d="M9 17l1-3 6-6 2 2-6 6Z" />
    </>
  ),
  // Thinking — a trailing ellipsis
  thinking: (
    <>
      <circle cx="6" cy="17" r="1.3" fill="currentColor" stroke="none" />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="18" cy="7" r="1.7" fill="currentColor" stroke="none" />
    </>
  ),
  // Sprout — just getting started
  sprout: (
    <>
      <path d="M12 21v-9" />
      <path d="M12 12c0-4-3-6-7-6 0 4 3 6 7 6Z" />
      <path d="M12 12c0-3 2-5 5-5 0 3-2 5-5 5Z" />
    </>
  ),
  // Counter-argument — a reversing loop
  counter: (
    <>
      <path d="M4 12a8 8 0 0 1 14-5" />
      <path d="M15 3v4h-4" />
      <path d="M20 12a8 8 0 0 1-14 5" />
      <path d="M9 21v-4h4" />
    </>
  ),
  // Fit / link — two shapes joined
  link: (
    <>
      <rect x="3" y="3" width="8" height="8" rx="2" />
      <rect x="13" y="13" width="8" height="8" rx="2" />
      <path d="M11 11l2 2" />
    </>
  ),
  // Sun — light mode
  sun: (
    <>
      <circle cx="12" cy="12" r="4.5" />
      <path d="M12 2.5v2.5" />
      <path d="M12 19v2.5" />
      <path d="M21.5 12H19" />
      <path d="M5 12H2.5" />
      <path d="M18.4 5.6l-1.8 1.8" />
      <path d="M7.4 16.6l-1.8 1.8" />
      <path d="M18.4 18.4l-1.8-1.8" />
      <path d="M7.4 7.4 5.6 5.6" />
    </>
  ),
  // Moon — dark mode
  moon: <path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5Z" />,
  // Trend — improving
  trendUp: (
    <>
      <path d="M5 16 15 6" />
      <path d="M8 6h7v7" />
    </>
  ),
  // Trend — declining
  trendDown: (
    <>
      <path d="M5 6 15 16" />
      <path d="M8 16h7v-7" />
    </>
  ),
  // Trend — flat
  trendFlat: (
    <>
      <path d="M4 12h14" />
      <path d="M14 8l4 4-4 4" />
    </>
  ),
  // Checkmark
  check: <path d="M5 12.5 9.5 17 19 7" />,
  // Chevron — expand/collapse
  chevronRight: <path d="M8.5 5 15.5 12 8.5 19" />,
};

export type IconName = keyof typeof PATHS;

interface IconProps {
  name: IconName;
  size?: number;
}

export default function Icon({ name, size = 18 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {PATHS[name]}
    </svg>
  );
}
