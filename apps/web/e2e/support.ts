import { readFileSync } from "node:fs";
import { resolve } from "node:path";

export function dashboardOracle(): Record<string, unknown> {
  return JSON.parse(
    readFileSync(
      resolve(process.cwd(), "fixtures/expected/dashboard_overview_v1.json"),
      "utf-8",
    ),
  ) as Record<string, unknown>;
}
