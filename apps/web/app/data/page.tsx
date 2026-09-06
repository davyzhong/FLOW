import { DataWorkbench } from "../../components/data/data-workbench";
import { AppShell } from "../../components/shell/app-shell";

export const metadata = { title: "数据工作台 | FLOW" };

export default function DataPage() {
  return (
    <AppShell>
      <DataWorkbench />
    </AppShell>
  );
}
