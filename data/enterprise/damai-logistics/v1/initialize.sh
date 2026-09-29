#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ] || { [ "$1" != "full" ] && [ "$1" != "business" ]; }; then
  echo "用法: $0 full|business" >&2
  exit 2
fi

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../../../../" && pwd)
cd "$repo_root"
exec uv run --project services/api python scripts/initialize_enterprise_package.py "$1"
