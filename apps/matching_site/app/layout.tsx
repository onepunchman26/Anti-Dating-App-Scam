import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI-SlowMatch · 慢慢相识",
  description: "Your conversation, your choices, your pace. / 你的对话、你的选择、你的节奏。",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
