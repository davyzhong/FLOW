#!/usr/bin/env python3
"""Unified documentation check entrypoint (plan Task 3 / M1.1, design V1.1 §6.3).

唯一检查入口：按迁移阶段显式聚合校验，供本地与 CI 使用。

    python3 scripts/check_docs.py --phase m1   # metadata + M0 基线 + 唯一入口
    python3 scripts/check_docs.py --phase m2   # m1 + 来源基线 + 知识发布
    python3 scripts/check_docs.py --phase m6   # m2 + 链接/兼容/读者测试（M5/M6 交付）

fail-closed：请求的阶段所依赖的模块或输入缺失时，非零退出，不静默跳过。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.documentation import inventory  # noqa: E402
from scripts.documentation.metadata import check_repository  # noqa: E402

PHASES = ("m1", "m2", "m6")


def _run_metadata(root: Path, errors: list) -> None:
    result = check_repository(root)
    print(f"metadata: {'PASS' if result.ok else 'FAIL'} "
          f"({result.checked} docs, {result.exempt} legacy-exempt, "
          f"{len(result.errors)} errors)")
    errors.extend(result.errors)


def _run_m0_baseline(root: Path, errors: list) -> None:
    baseline = root / "docs/knowledge-base/00_governance/migration/baseline.yaml"
    if not baseline.is_file():
        errors.append("M0 baseline.yaml 缺失（migration 基线未冻结）")
        return
    code = inventory.check_baseline(root, baseline)
    if code != 0:
        errors.append("M0 基线 --check 失败（checkpoint tree 不可重放）")


def _run_source_and_release(root: Path, errors: list) -> None:
    baseline = root / "docs/knowledge-base/00_governance/migration/source-baseline.tsv"
    hash_file = root / "docs/knowledge-base/00_governance/migration/source-baseline.sha256"
    if not baseline.is_file() or not hash_file.is_file():
        errors.append("source-baseline 缺失（Task 2 Step 5c 未闭合）")
    else:
        from scripts.documentation.source_baseline import check as sb_check

        try:
            sb_check(root, baseline, hash_file)
            print("source baseline: PASS")
        except ValueError as exc:
            errors.append(f"source baseline: {exc}")
    current = root / "docs/knowledge-base/00_governance/releases/CURRENT_RELEASE"
    if current.is_file():
        from scripts.documentation.metadata import check_release_lock

        release_id = current.read_text(encoding="utf-8").strip()
        rel_errors = check_release_lock(root, release_id)
        print(f"release {release_id}: {'PASS' if not rel_errors else 'FAIL'}")
        errors.extend(rel_errors)
    else:
        print("release: 尚未创建 CURRENT_RELEASE（M2 激活前为预期状态）")


def _run_m6_modules(root: Path, errors: list) -> None:
    for rel in ("scripts/documentation/links.py",
                "scripts/documentation/reader_rubric.py",
                "docs/80_reviews/reader-test/RUBRIC--v1.0.yaml"):
        if not (root / rel).is_file():
            errors.append(f"m6 依赖缺失（M5/M6 交付物）：{rel}")


def run_phase(root: Path, phase: str) -> int:
    errors: list = []
    _run_metadata(root, errors)
    _run_m0_baseline(root, errors)
    if phase in ("m2", "m6"):
        _run_source_and_release(root, errors)
    if phase == "m6":
        _run_m6_modules(root, errors)
    for e in errors:
        print(f"ERROR {e}")
    print(f"phase {phase}: {'PASS' if not errors else 'FAIL'}")
    return 0 if not errors else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase", choices=PHASES, required=True)
    args = ap.parse_args(argv)
    return run_phase(ROOT, args.phase)


if __name__ == "__main__":
    sys.exit(main())
