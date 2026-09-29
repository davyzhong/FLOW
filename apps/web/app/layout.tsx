import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Providers } from "./providers";

import "@fontsource-variable/inter";
import "@fontsource-variable/jetbrains-mono";
import "@fontsource-variable/noto-sans-sc";
import "./globals.css";
import "../components/dashboard/dashboard.css";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "FLOW",
  description: "Finance BP 经营分析工作台",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  // 根布局只承担文档骨架与全局 provider；认证 UI（退出入口）在 AppShell 侧栏，
  // /login 是唯一无 AppShell 路由，因此不会出现全局孤立退出按钮。
  return (
    <html lang="zh-CN">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
