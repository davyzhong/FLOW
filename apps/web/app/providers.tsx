"use client";

import { useState, type ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";

import { createFlowQueryClient } from "../lib/api/query-client";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(createFlowQueryClient);
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
