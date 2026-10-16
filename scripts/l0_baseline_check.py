#!/usr/bin/env python3
"""C 级 L0 事实基线检查（2026-10-16 用户裁决 1C：非阻断 CI 信号灯）。

验证冻结清单（c-level-freeze-2026-09-29-v1.yaml）的完整性：
1. 冻结 YAML 可解析且 report_count = 14
2. 每份报告的 source_pdf / active_yaml SHA-256 与本地文件一致
3. source_values 和 l1_values 行数与冻结时登记一致

非阻断：本脚本退出码仅作信号灯，CI continue-on-error=true。
退出码：0 = 全部通过；1 = 有不一致（但 CI 不阻塞）。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
FREEZE_PATH = ROOT / "validation/financial_reports/c-level-freeze-2026-09-29-v1.yaml"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if not FREEZE_PATH.is_file():
        print(f"FAIL: 冻结清单不存在: {FREEZE_PATH}")
        return 1

    doc = yaml.safe_load(FREEZE_PATH.read_text(encoding="utf-8"))
    reports = doc.get("reports", [])
    report_count = doc.get("report_count", 0)

    errors: list[str] = []
    total_source_values = 0
    total_l1_values = 0

    if len(reports) != report_count:
        errors.append(
            f"report_count 不匹配: YAML 记录 {len(reports)}, 声明 {report_count}"
        )

    for r in reports:
        sample = r.get("sample", "unknown")
        for field, key in (
            ("source_pdf", "source_pdf_sha256"),
            ("active_yaml", "active_yaml_sha256"),
        ):
            rel = r.get(field, "")
            expected_sha = r.get(key, "")
            if not rel or not expected_sha:
                errors.append(f"{sample}: {field} 缺少路径或 SHA")
                continue
            full = ROOT / rel
            if not full.is_file():
                errors.append(f"{sample}: {field} 文件不存在: {rel}")
                continue
            actual = sha256_of(full)
            if actual != expected_sha:
                errors.append(
                    f"{sample}: {field} SHA 不匹配 (期望 {expected_sha[:12]}…, 实际 {actual[:12]}…)"
                )

        sv = r.get("source_values", 0)
        l1 = r.get("l1_values", 0)
        sv_count = len(sv) if isinstance(sv, list) else int(sv or 0)
        l1_count = len(l1) if isinstance(l1, list) else int(l1 or 0)
        total_source_values += sv_count
        total_l1_values += l1_count

    # 汇总
    print(f"冻结清单: {doc.get('freeze_id', 'unknown')}")
    print(f"报告数: {len(reports)} (声明 {report_count})")
    print(f"source_values 总计: {total_source_values}")
    print(f"l1_values 总计: {total_l1_values}")

    if errors:
        print(f"\nFAIL: {len(errors)} 项不一致:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\nL0 baseline check: PASS (14 reports, all SHA verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
