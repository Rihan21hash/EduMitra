import type { Metadata } from "next";
import { Inter, Noto_Sans_Devanagari } from "next/font/google";
import { site, theme } from "@/content";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const notoDevanagari = Noto_Sans_Devanagari({
  subsets: ["devanagari"],
  variable: "--font-noto-devanagari",
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: `${site.name.en} — ${site.tagline.en}`,
  description: site.fullName.en,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="mr"
      suppressHydrationWarning
      className={`${inter.variable} ${notoDevanagari.variable} h-full`}
      style={{
        ["--brand" as any]: theme.brand,
        ["--accent" as any]: theme.accent,
        ["--surface" as any]: theme.surface,
        ["--text" as any]: theme.text,
        ["--border" as any]: theme.border,
      }}
    >
      <body suppressHydrationWarning className="min-h-full flex flex-col font-sans bg-[var(--surface)] text-[var(--text)]">
        {children}
      </body>
    </html>
  );
}
