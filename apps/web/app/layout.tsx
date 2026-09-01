import type { Metadata } from "next";
import type { ReactNode } from "react";

import "@fontsource-variable/inter";
import "@fontsource-variable/jetbrains-mono";
import "@fontsource-variable/noto-sans-sc";
import "./globals.css";
import "../components/dashboard/dashboard.css";

export const metadata: Metadata = {
  title: "FLOW",
  description: "Finance BP 经营分析工作台",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
