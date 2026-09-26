import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "TopTenUG — Uganda, ranked by data",
  description: "Evidence-driven quarterly rankings across Uganda's technology and digital ecosystem.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <nav className="nav">
            <a className="brand" href="/">TOPTENUG 🇺🇬</a>
            <a className="pill" href="/methodology/devrankug-v1">Transparent methodology</a>
          </nav>
          {children}
        </div>
      </body>
    </html>
  );
}
