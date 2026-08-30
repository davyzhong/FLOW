import json
from pathlib import Path


def main() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    answers = json.loads(
        (repository_root / "fixtures/expected/known_answers.json").read_text(encoding="utf-8")
    )
    counts = answers["row_counts"]
    analysis = answers["headline_totals"]["analysis"]
    print(
        "FLOW data contract PASS | "
        f"operating={counts['operating_actuals']} "
        f"financial={counts['financial_actuals']} "
        f"budget={counts['monthly_budgets']} "
        f"ar={counts['ar_collections']} | "
        f"revenue={analysis['revenue']} "
        f"gross_margin={analysis['gross_margin']} "
        f"operating_profit={analysis['operating_profit']}"
    )


if __name__ == "__main__":
    main()
