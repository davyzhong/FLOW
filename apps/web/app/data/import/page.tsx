import { AppShell } from "../../../components/shell/app-shell";
import { ImportWizard } from "../../../components/data/import-wizard";

export const metadata = { title: "真实数据导入 | FLOW" };

export default function DataImportPage() {
  return (
    <AppShell>
      <ImportWizard />
    </AppShell>
  );
}
