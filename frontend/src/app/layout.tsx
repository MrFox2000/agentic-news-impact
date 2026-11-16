import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "News → Price Impact",
  description:
    "An agent that reads the news, checks what the price did next, and cites the headlines it used.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-dvh antialiased">{children}</body>
    </html>
  );
}
