import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ECP Studio",
  description:
    "Enterprise Context Platform — the meaning layer for AI systems on enterprise data.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
