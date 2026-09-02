# -*- coding: utf-8 -*-
"""重新生成 docs/knowledge-base/99_manifest/inventory.tsv 与 sha256sums.txt。

格式与既有清单保持一致：
- inventory.tsv: relative_path<TAB>size_bytes<TAB>modified_time<TAB>mime_type
- sha256sums.txt: <sha256>  ./<relative_path>
路径均相对知识库根目录，排序一致。
"""

from __future__ import annotations

import hashlib
import sys
from datetime import datetime
from pathlib import Path

KB_DIR = Path(__file__).resolve().parents[2] / "docs" / "knowledge-base"

HEADER = "relative_path\tsize_bytes\tmodified_time\tmime_type"
GENERATED_MANIFEST_PATHS = frozenset(
    {
        "99_manifest/inventory.tsv",
        "99_manifest/sha256sums.txt",
    }
)


def build(kb_dir: Path = KB_DIR) -> tuple[int, int]:
    rows = []
    hashes = []
    for path in sorted(kb_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(kb_dir).as_posix()
        if rel in GENERATED_MANIFEST_PATHS:
            continue
        stat = path.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds")
        rows.append("%s\t%d\t%s\tapplication/octet-stream" % (rel, stat.st_size, mtime))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes.append("%s  ./%s" % (digest, rel))
    (kb_dir / "99_manifest" / "inventory.tsv").write_text(
        HEADER + "\n" + "\n".join(rows) + "\n", encoding="utf-8"
    )
    (kb_dir / "99_manifest" / "sha256sums.txt").write_text("\n".join(hashes) + "\n", encoding="utf-8")
    return len(rows), len(hashes)


if __name__ == "__main__":
    kb = Path(sys.argv[1]) if len(sys.argv) > 1 else KB_DIR
    n_rows, n_hashes = build(kb)
    print("inventory rows=%d, sha256 lines=%d" % (n_rows, n_hashes))
