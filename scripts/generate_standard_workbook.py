import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "services/api/src"))

from flow_api.data_contract.contract import load_contract  # noqa: E402
from flow_api.data_contract.workbook import render_workbook  # noqa: E402
from flow_api.fixtures.generator import build_reference_package  # noqa: E402


def main() -> None:
    contract = load_contract(REPOSITORY_ROOT / "templates/excel/flow_v1_contract.yaml")
    render_workbook(
        contract,
        build_reference_package(),
        REPOSITORY_ROOT / "fixtures/workbooks/flow_standard_v1.xlsx",
    )


if __name__ == "__main__":
    main()
