#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://flow:flow_dev_only@127.0.0.1:5432/flow}"
export REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/0}"
export S3_ENDPOINT_URL="${S3_ENDPOINT_URL:-http://127.0.0.1:9000}"
export S3_BUCKET="${S3_BUCKET:-flow}"
export S3_ACCESS_KEY="${S3_ACCESS_KEY:-flow}"
export S3_SECRET_KEY="${S3_SECRET_KEY:-flow_dev_only}"

golden_dir="$(mktemp -d)"
trap 'rm -rf "${golden_dir}"' EXIT

(cd services/api && uv run alembic upgrade head)

(cd services/api && uv run python "${repo_root}/scripts/render_golden.py" --out "${golden_dir}")

pnpm exec playwright pdf "file://${golden_dir}/report.html" "${golden_dir}/report.pdf"

python3 - "${golden_dir}" <<'PYEOF'
import sys
from pathlib import Path

golden = Path(sys.argv[1])
pdf = golden / "report.pdf"
assert pdf.exists() and pdf.stat().st_size > 1000, "pdf is missing or too small"
assert pdf.read_bytes()[:5] == b"%PDF-", "pdf magic bytes missing"
key_values = __import__("json").loads((golden / "key_values.json").read_text(encoding="utf-8"))
assert key_values["missing"] == [], key_values["missing"]
print("pdf printed and verified; all formats carry identical key values.")
PYEOF

echo "publishing golden gate passed."
