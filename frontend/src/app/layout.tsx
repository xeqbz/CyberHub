import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "CyberHub",
  description: "Esports tournament platform",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru">
      <body>
        <div className="bg-orb orb-1" />
        <div className="bg-orb orb-2" />
        <div className="bg-grid" />
        <div className="app-shell">{children}</div>
      </body>
    </html>
  );
}