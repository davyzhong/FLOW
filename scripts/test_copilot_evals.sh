#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
cd services/api
uv run pytest tests/copilot -q
uv run python - <<'PYEOF'
from flow_api.copilot.evals import run_all

results = run_all()
failed = [result for result in results if not result.passed]
for result in results:
    print(f"{result.case_id}: {'PASS' if result.passed else 'FAIL ' + result.detail}")
if failed:
    raise SystemExit(f"{len(failed)} copilot eval cases failed")
print(f"All {len(results)} copilot eval cases passed.")
PYEOF
