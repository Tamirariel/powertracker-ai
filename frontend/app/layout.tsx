import type { Metadata } from "next";
import { Rubik, Oswald } from "next/font/google";
import "./globals.css";
import Nav from "./components/Nav";

// Rubik — כל הממשק בעברית. גופן משתנה, כל המשקלים 300–900 זמינים.
const rubik = Rubik({
  variable: "--font-rubik",
  subsets: ["hebrew", "latin"],
  display: "swap",
});

// Oswald — מספרים בלבד. צר וגבוה, כמו לוח תוצאות בתחרות.
const oswald = Oswald({
  variable: "--font-oswald",
  subsets: ["latin"],
  display: "swap",
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
      className={`${rubik.variable} ${oswald.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-base text-ink">
        <Nav />
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}