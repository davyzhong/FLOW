#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
temporary_dir="$(mktemp -d)"
trap 'rm -rf "$temporary_dir"' EXIT

cp "$repo_root/packages/contracts/openapi.json" "$temporary_dir/openapi.json"
cp "$repo_root/packages/contracts/src/schema.d.ts" "$temporary_dir/schema.d.ts"

"$repo_root/scripts/generate_contracts.sh"

diff -u "$temporary_dir/openapi.json" "$repo_root/packages/contracts/openapi.json"
diff -u "$temporary_dir/schema.d.ts" "$repo_root/packages/contracts/src/schema.d.ts"
