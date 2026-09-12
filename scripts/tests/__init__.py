"""Test package for FLOW documentation governance tooling.

修补 sys.path，使测试可从任意工作目录运行
（仓库根 `python -m unittest discover -s scripts/tests` 与
`cd services/api && uv run python -m unittest discover -s ../../scripts/tests` 等价）。
"""

import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
