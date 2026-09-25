"""测试库隔离契约测试（G2 安全门禁）。

- 本地（非 CI、无豁免）：DATABASE_URL 指向常驻 flow 库时必须被切换到 flow_test；
- 豁免通道：FLOW_TEST_ALLOW_PERSISTENT_DB=1 或 GITHUB_ACTIONS=true 不切换；
- 非 flow 库名（如已指向 flow_test 或其他）不干预；
- DB 不可达时静默跳过（unit 场景）。
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from unittest import mock

CONFTEST = Path(__file__).resolve().parents[0] / "conftest.py"


def _reload_conftest_with(env: dict[str, str]) -> str:
    """以给定环境重执行 conftest 的隔离逻辑，返回生效的 DATABASE_URL。"""

    code = CONFTEST.read_text(encoding="utf-8")
    switch_src = code[code.index("def _switch_to_isolated_test_database") :]
    switch_src = switch_src[: switch_src.index("os.environ.setdefault(\"FLOW_ENV\"")]

    with mock.patch.dict(os.environ, env, clear=False):
        # 重新执行头部环境默认值 + 切换函数（不导入 pytest fixture 部分）
        header_end = code.index("def _switch_to_isolated_test_database")
        header = code[:header_end]
        namespace: dict[str, object] = {}
        exec(compile(header, "conftest-header", "exec"), namespace)  # noqa: S102
        exec(compile(switch_src, "conftest-switch", "exec"), namespace)  # noqa: S102
        namespace["_switch_to_isolated_test_database"]()  # type: ignore[operator]
        return os.environ["DATABASE_URL"]


def test_local_default_switches_flow_to_flow_test() -> None:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        return  # CI 内该场景按设计豁免，不适用
    env = {
        "DATABASE_URL": "postgresql+psycopg://flow:flow_dev_only@localhost:5432/flow",
        "FLOW_TEST_ALLOW_PERSISTENT_DB": "",
    }
    result = _reload_conftest_with(env)
    assert result.endswith("/flow_test"), f"本地默认必须切换 flow_test，实际 {result}"


def test_explicit_optout_keeps_persistent() -> None:
    env = {
        "DATABASE_URL": "postgresql+psycopg://flow:flow_dev_only@localhost:5432/flow",
        "FLOW_TEST_ALLOW_PERSISTENT_DB": "1",
    }
    result = _reload_conftest_with(env)
    assert result.endswith("/flow"), "显式豁免必须保留原库"


def test_github_actions_env_is_exempt() -> None:
    env = {
        "DATABASE_URL": "postgresql+psycopg://flow:flow_dev_only@localhost:5432/flow",
        "GITHUB_ACTIONS": "true",
    }
    result = _reload_conftest_with(env)
    assert result.endswith("/flow"), "CI 环境豁免切换"


def test_non_flow_database_untouched() -> None:
    env = {
        "DATABASE_URL": "postgresql+psycopg://flow:pw@localhost:5432/some_other_db",
    }
    result = _reload_conftest_with(env)
    assert result.endswith("/some_other_db"), "非 flow 库名不干预"


def test_unreachable_db_skips_silently() -> None:
    env = {
        "DATABASE_URL": "postgresql+psycopg://flow:flow_dev_only@127.0.0.1:1/flow",
    }
    result = _reload_conftest_with(env)
    # DB 不可达：跳过切换，URL 保持原样（unit 场景不依赖 DB）
    assert result.endswith("@127.0.0.1:1/flow")
