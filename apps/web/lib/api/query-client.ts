"use client";

// F-Query：TanStack Query 客户端工厂（统一默认值，测试与运行时共用）。
// retry=false：财报/快照语义下静默重试会掩盖 503 门禁反馈；
// refetchOnWindowFocus=false：页面数据为冻结快照，焦点切换不应隐式重取。
import { QueryClient } from "@tanstack/react-query";

export function createFlowQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        refetchOnWindowFocus: false,
      },
      mutations: {
        retry: false,
      },
    },
  });
}
