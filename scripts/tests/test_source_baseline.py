"""Task 1 (M0.1) tests: source baseline build/check (plan Step 5).

来源级基线：固定输入清单 → 逐条 source_id 行；验证必填字段、
snapshot ID、count（含批准订正）、UTF-8 排序、逐行稳定身份、
文件自身 SHA-256 与 baseline.yaml 引用。
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import json

from scripts.documentation.source_baseline import build, build_v2, check

HEADER = [
    "source_id", "snapshot_id", "locator", "title", "author", "bytes",
    "sha256", "duplicate_group", "k_route", "availability", "evidence_path",
]


def make_fixture(tmp: Path) -> Path:
    """微信移交档案 2 篇 + 扫描登记 TSV 3 条 = 5 条来源。"""
    import subprocess

    for rel, body in {
        "kb/08_wechat_sources/x/2024a_文章一/article.md": "article one\n",
        "kb/08_wechat_sources/x/2024b_文章二/article.md": "article two\n",
    }.items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    meta = tmp / "kb/08_wechat_sources/x/2024a_文章一/meta.json"
    meta.write_text('{"title": "文章一", "author": "甲"}\n', encoding="utf-8")

    scan = tmp / "migration/scan-entries.tsv"
    scan.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        ["source_id", "locator", "title", "author", "k_route", "availability", "evidence_path", "duplicate_group"],
        ["scan-001", "vault:/processed/微信知识库/甲/1.md", "扫描来源一", "", "K4", "locator-only", "scan/W1.md", ""],
        ["scan-002", "vault:/processed/微信知识库/乙/2.md", "扫描来源二", "", "K3", "locator-only", "scan/W2.md", ""],
        ["scan-003", "vault:/wiki/经营分析.md", "扫描来源三", "丙", "K4", "locator-only", "scan/D-wiki.md", ""],
    ]
    with open(scan, "w", encoding="utf-8", newline="") as f:
        import csv

        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerows(rows)

    inputs = tmp / "source-inputs.yaml"
    inputs.write_text(
        "snapshot_id: obsidian-test-2026\n"
        "expected_count: 5\n"
        "corrections: []\n"
        "groups:\n"
        "  - id: wechat-archive\n"
        "    type: wechat-archive-dir\n"
        "    root: kb/08_wechat_sources/x\n"
        "    pattern: '**/article.md'\n"
        "  - id: scan-entries\n"
        "    type: entries-tsv\n"
        "    path: migration/scan-entries.tsv\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "add", "kb"], cwd=tmp, check=True)
    return tmp


class SourceBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_fixture(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _build(self, expected: int = 5, corrections: str = "[]") -> Path:
        inputs = self.root / "source-inputs.yaml"
        text = inputs.read_text(encoding="utf-8")
        text = text.replace("expected_count: 5", f"expected_count: {expected}")
        text = text.replace("corrections: []", f"corrections: {corrections}")
        inputs.write_text(text, encoding="utf-8")
        out = self.root / "out/source-baseline.tsv"
        build(self.root, inputs, "obsidian-test-2026", expected, out)
        return out

    def test_build_writes_sorted_unique_rows(self) -> None:
        out = self._build()
        lines = out.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0].split("\t"), HEADER)
        ids = [ln.split("\t")[0] for ln in lines[1:]]
        self.assertEqual(len(ids), 5)
        self.assertEqual(len(set(ids)), 5)
        self.assertEqual(ids, sorted(ids))
        # 每行 snapshot_id 固定、字段数一致
        for ln in lines[1:]:
            fields = ln.split("\t")
            self.assertEqual(len(fields), len(HEADER))
            self.assertEqual(fields[1], "obsidian-test-2026")
        # wechat 条目 availability=full-text-in-repo 且有内容指纹
        wechat = [ln for ln in lines[1:] if ln.split("\t")[0].startswith("wechat-")]
        self.assertEqual(len(wechat), 2)
        for ln in wechat:
            self.assertEqual(ln.split("\t")[9], "full-text-in-repo")
            self.assertEqual(len(ln.split("\t")[6]), 64)

    def test_build_is_deterministic(self) -> None:
        a = self._build().read_bytes()
        b = self._build().read_bytes()
        self.assertEqual(a, b)

    def test_build_rejects_count_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            self._build(expected=6)

    def test_build_allows_approved_correction(self) -> None:
        out = self._build(expected=4, corrections='[{"reason": "new sync batch", "delta": 1}]')
        self.assertEqual(len(out.read_text(encoding="utf-8").splitlines()) - 1, 5)

    def test_build_rejects_duplicate_source_id(self) -> None:
        scan = self.root / "migration/scan-entries.tsv"
        text = scan.read_text(encoding="utf-8")
        # 把 scan-003 的 ID 改成与 scan-001 重复 → 必须拒绝
        text = text.replace("scan-003", "scan-001")
        scan.write_text(text, encoding="utf-8")
        with self.assertRaises(ValueError):
            self._build()

    def test_check_passes_on_fresh_build(self) -> None:
        out = self._build()
        hash_file = self.root / "out/source-baseline.sha256"
        from scripts.documentation.source_baseline import write_hash_file

        write_hash_file(out, hash_file)
        self.assertTrue(check(self.root, out, hash_file))

    def test_check_fails_on_tampered_row(self) -> None:
        out = self._build()
        hash_file = self.root / "out/source-baseline.sha256"
        from scripts.documentation.source_baseline import write_hash_file

        write_hash_file(out, hash_file)
        tampered = out.read_text(encoding="utf-8").replace("扫描来源一", "篡改标题")
        out.write_text(tampered, encoding="utf-8")
        with self.assertRaises(ValueError):
            check(self.root, out, hash_file)

    def test_check_fails_on_stale_hash_file(self) -> None:
        out = self._build()
        hash_file = self.root / "out/source-baseline.sha256"
        from scripts.documentation.source_baseline import write_hash_file

        write_hash_file(out, hash_file)
        out.write_text(out.read_text(encoding="utf-8") + "extra-row\tx\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            check(self.root, out, hash_file)

    def test_build_v2_normalizes_text_strips_machine_appendices_and_is_deterministic(self) -> None:
        vault = self.root / "vault"
        source = vault / "processed/03_财务与会计/利润率.md"
        source.parent.mkdir(parents=True)
        source.write_text("# 毛利率\r\n正文 e\u0301。\r\n%%davybase-summary-begin%%\r\n机器摘要\r\n%%davybase-summary-end%%\r\n", encoding="utf-8")
        (vault / "processed/03_财务与会计/图.png").write_bytes(b"image")
        manifest = self.root / "accepted.json"
        manifest.write_text(json.dumps({"status":"accepted","snapshot_id":"snap-1","snapshot_kind":"working_tree","candidate":{"head":"abc","tree":"tree"},"verification":{"content_sha256":"x"}}), encoding="utf-8")
        inputs = self.root / "inputs.yaml"
        inputs.write_text("snapshot_id: snap-1\nvault_root: '" + str(vault) + "'\nsource_roots: [\"processed/03_财务与会计\"]\n", encoding="utf-8")
        registry = self.root / "registry.tsv"
        baseline = self.root / "baseline.tsv"
        diff = self.root / "diff.tsv"
        result = build_v2(manifest, inputs, registry, baseline, diff, self.root / "none.tsv")
        first = (baseline.read_bytes(), registry.read_bytes(), diff.read_bytes())
        result2 = build_v2(manifest, inputs, registry, baseline, diff, self.root / "none.tsv")
        self.assertEqual(first, (baseline.read_bytes(), registry.read_bytes(), diff.read_bytes()))
        self.assertEqual(result, result2)
        text = baseline.read_text(encoding="utf-8")
        import hashlib
        self.assertEqual(text.splitlines()[1].split("\t")[6], hashlib.sha256("# 毛利率\n正文 é。\n\n".encode("utf-8")).hexdigest())
        self.assertEqual(len(result), 1)
        self.assertEqual(diff.read_text(encoding="utf-8").splitlines()[1].split("\t")[5], r"\N")

    def test_build_v2_rejects_nonaccepted_manifest_and_duplicate_registry_identity(self) -> None:
        manifest = self.root / "bad.json"
        manifest.write_text(json.dumps({"status":"rejected","snapshot_kind":"working_tree"}), encoding="utf-8")
        inputs = self.root / "inputs.yaml"
        inputs.write_text("snapshot_id: snap-1\nvault_root: /tmp\nsource_roots: [\"wiki\"]\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            build_v2(manifest, inputs, self.root / "registry.tsv", self.root / "base.tsv", self.root / "diff.tsv", self.root / "old.tsv")

    def test_build_v2_reports_body_and_enrichment_changes_without_false_positives(self) -> None:
        vault = self.root / "vault"
        source = vault / "processed/03_财务与会计/利润率.md"
        source.parent.mkdir(parents=True)
        source.write_text("# 毛利率\n旧正文\n", encoding="utf-8")
        import hashlib
        old_body_hash = hashlib.sha256("# 毛利率\n旧正文\n".encode("utf-8")).hexdigest()
        old = self.root / "old.tsv"
        old.write_text("source_id\tlocator\tbody_sha256\timage_set_sha256\thas_summary_appendix\thas_image_appendix\n"
                       f"legacy-1\tvault:processed/03_财务与会计/利润率.md\t{old_body_hash}\timages0\tfalse\tfalse\n", encoding="utf-8")
        manifest = self.root / "accepted.json"
        manifest.write_text(json.dumps({"status":"accepted","snapshot_id":"snap-1","snapshot_kind":"working_tree","candidate":{"head":"abc","tree":"tree"}}), encoding="utf-8")
        inputs = self.root / "inputs.yaml"
        inputs.write_text("snapshot_id: snap-1\nvault_root: '" + str(vault) + "'\nsource_roots: [\"processed/03_财务与会计\"]\n", encoding="utf-8")
        source.write_text("# 毛利率\n新正文\n%%davybase-summary-begin%%\n摘要\n%%davybase-summary-end%%\n", encoding="utf-8")
        diff = self.root / "diff.tsv"
        build_v2(manifest, inputs, self.root / "registry.tsv", self.root / "base.tsv", diff, old)
        fields = diff.read_text(encoding="utf-8").splitlines()[1].split("\t")
        self.assertEqual(fields[0], "legacy-1")
        self.assertEqual(fields[1:5], ["present", "false", "true", "true"])


if __name__ == "__main__":
    unittest.main()
