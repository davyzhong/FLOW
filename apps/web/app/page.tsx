import { DashboardApp } from "../components/dashboard/dashboard-app";
import { AppShell } from "../components/shell/app-shell";
import type { DashboardFilters } from "../lib/api/client";
import { DASHBOARD_FILTER_KEYS } from "../lib/deep-links";

function first(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) return value[0] ?? null;
  return value ?? null;
}

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = await searchParams;
  const initialFilters: DashboardFilters = {};
  for (const key of DASHBOARD_FILTER_KEYS) {
    const value = first(query[key]);
    if (value) initialFilters[key] = value;
  }
  return (
    <AppShell>
      <DashboardApp initialFilters={initialFilters} />
    </AppShell>
  );
}
