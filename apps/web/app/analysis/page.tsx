import { FourQuestionWorkbench } from "../../components/analysis/four-question-workbench";
import { AppShell } from "../../components/shell/app-shell";

export const metadata = { title: "四问工作台 | FLOW" };

export default function AnalysisPage() {
  return (
    <AppShell>
      <FourQuestionWorkbench />
    </AppShell>
  );
}
