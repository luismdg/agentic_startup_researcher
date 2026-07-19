"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Icon, { type IconName } from "@/components/ui/Icon/Icon";
import styles from "./Sidebar.module.css";

const NAV_ITEMS: { href: string; label: string; icon: IconName }[] = [
  { href: "/", label: "Overview", icon: "grid" },
  { href: "/thesis", label: "My Focus", icon: "focus" },
  { href: "/sourcing", label: "Discover", icon: "discover" },
  { href: "/evaluate", label: "Evaluate", icon: "scorecard" },
  { href: "/trust", label: "Fact Check", icon: "factcheck" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className={styles.sidebar} aria-label="Primary">
      <div className={styles.brand}>
        <span className={styles.brandMark}>VC</span>
        <span className={styles.brandName}>Brain</span>
      </div>
      <ul className={styles.list}>
        {NAV_ITEMS.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={`${styles.link} ${active ? styles.active : ""}`}
              >
                <span className={styles.icon}>
                  <Icon name={item.icon} size={17} />
                </span>
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
      <div className={styles.footer}>
        <span className={styles.footerLabel}>Mock data · demo build</span>
      </div>
    </nav>
  );
}
