import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Link from "next/link";
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PowerTracker",
  description: "יומן אימונים חכם וניתוח פאוורליפטינג",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="he"
      dir="rtl"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <nav className="flex gap-4 border-b border-white/10 px-8 py-3 text-sm">
          <Link href="/journal" className="hover:text-blue-400">יומן</Link>
          <Link href="/chat" className="hover:text-blue-400">צ׳אט</Link>
        </nav>
        {children}
      </body>
    </html>
  );
}
