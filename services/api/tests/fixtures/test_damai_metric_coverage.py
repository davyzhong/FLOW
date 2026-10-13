from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
DICTIONARY_PATH = REPOSITORY_ROOT / "config/metrics/metric_dictionary_v1_1.yaml"
COVERAGE_PATH = REPOSITORY_ROOT / "config/metrics/damai_demo_metric_coverage_v1.yaml"
GENERATOR_PATH = REPOSITORY_ROOT / "scripts/build_damai_metric_coverage.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("build_damai_metric_coverage", GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_damai_coverage_is_generated_from_current_metric_dictionary() -> None:
    dictionary = yaml.safe_load(DICTIONARY_PATH.read_text(encoding="utf-8"))
    coverage = yaml.safe_load(COVERAGE_PATH.read_text(encoding="utf-8"))

    assert coverage["synthetic"] is True
    assert coverage["dictionary_id"] == dictionary["dictionary_id"]
    assert coverage["metrics_source"] == "config/metrics/metric_dictionary_v1_1.yaml"
    assert (
        coverage["metrics_source_sha256"]
        == hashlib.sha256(DICTIONARY_PATH.read_bytes()).hexdigest()
    )
    assert [row["metric_code"] for row in coverage["metrics"]] == [
        row["metric_code"] for row in dictionary["metrics_general"]
    ]
    assert {
        snapshot["period"]: (snapshot["computable"], snapshot["total"])
        for snapshot in coverage["snapshots"]
    } == {
        "FY2025": (42, 50),
        "FY2026": (45, 50),
    }


def test_current_dictionary_formulas_reconcile_on_damai_statements() -> None:
    generator = _load_generator()
    dictionary = yaml.safe_load(DICTIONARY_PATH.read_text(encoding="utf-8"))
    engine = generator.Engine(
        {"facts": generator.build_damai_facts()},
        dictionary,
    )
    company = "damai_syn"
    period = "FY2026"

    def metric(code: str) -> float:
        return engine.ev_metric(code, company, period)

    assert metric("interest_coverage") > 0
    assert (
        abs(metric("ccc_days") - (metric("dso_days") + metric("dio_days") - metric("dpo_days")))
        < 1e-9
    )
    assert (
        abs(
            metric("roe")
            - metric("net_margin") * metric("total_asset_turnover") * metric("equity_multiplier")
        )
        < 1e-9
    )

    facts = {
        (fact["item_id"], fact["role"]): fact["value"]
        for fact in generator.build_damai_facts()
        if fact["company"] == company and fact["period"] == period
    }
    expected_expense_ratio = sum(
        facts[(item_id, "cur")]
        for item_id in ("is.selling_exp", "is.admin_exp", "is.rnd_exp", "is.fin_exp")
    ) / facts[("is.revenue", "cur")]
    assert abs(metric("period_expense_ratio") - expected_expense_ratio) < 1e-9
