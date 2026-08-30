from pathlib import Path
from typing import Any

import yaml

from flow_api.data_contract.models import WorkbookContract


def load_contract(path: str | Path) -> WorkbookContract:
    contract_path = Path(path)
    with contract_path.open(encoding="utf-8") as contract_file:
        payload: Any = yaml.safe_load(contract_file)
    if not isinstance(payload, dict):
        raise ValueError(f"contract must be a YAML mapping: {contract_path}")
    return WorkbookContract.model_validate(payload)
