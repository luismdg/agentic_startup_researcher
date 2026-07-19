import type { Metadata } from "next";
import "./globals.css";
import styles from "./shell.module.css";
import Sidebar from "@/components/layout/Sidebar/Sidebar";
import TopBar from "@/components/layout/TopBar/TopBar";

export const metadata: Metadata = {
  title: "VC Brain",
  description: "Internal investor dashboard for sourcing, screening, diligence, and decisions.",
};

// Default theme is the cosmic (dark) look -- see the design-tokens comment
// in globals.css for why. "light" is the opt-in variant now.
const THEME_INIT_SCRIPT = `
(function () {
  try {
    var stored = window.localStorage.getItem("vc-brain-theme");
    document.documentElement.dataset.theme = stored === "light" ? "light" : "dark";
  } catch (e) {
    document.documentElement.dataset.theme = "dark";
  }
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body>
        <div className={styles.shell}>
          <Sidebar />
          <div className={styles.main}>
            <TopBar />
            <main className={styles.content}>{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
