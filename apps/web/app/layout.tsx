import type { Metadata } from "next";
import type { ReactNode } from "react";

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
  return (
    <html lang="zh-CN">
      <body>{children}
        {process.env.AUTH_TOKEN && <footer style={{ padding: 16, textAlign: "center" }}>
          <form action="/api/auth/logout" method="post"><button type="submit">退出登录</button></form>
        </footer>}
      </body>
    </html>
  );
}
