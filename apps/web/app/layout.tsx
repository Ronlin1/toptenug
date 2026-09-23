import type { ReactNode } from "react";

export const metadata = {
  title: "TopTenUG",
  description: "Uganda, ranked by data.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
