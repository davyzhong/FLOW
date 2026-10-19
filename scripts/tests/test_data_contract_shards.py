"""分片映射必须完整、互斥并覆盖两个原始测试目录。"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from scripts.data_contract_shards import SHARDS, all_test_files, validate_shards

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class DataContractShardTests(unittest.TestCase):
    def test_every_data_contract_and_fixture_test_file_is_assigned_once(self) -> None:
        self.assertEqual(validate_shards(), [])

    def test_shards_include_the_full_suite(self) -> None:
        assigned = [path for paths in SHARDS.values() for path in paths]
        self.assertEqual(len(assigned), len(all_test_files()))
        self.assertEqual(set(assigned), all_test_files())

    def test_workflow_runs_every_shard_and_keeps_the_stable_summary_job(self) -> None:
        workflow = yaml.safe_load((REPOSITORY_ROOT / ".github/workflows/ci.yml").read_text())
        jobs = workflow["jobs"]
        workflow_shards = jobs["data-contract-shards"]["strategy"]["matrix"]["shard"]
        self.assertEqual(set(workflow_shards), set(SHARDS))
        self.assertEqual(jobs["data-contract"]["needs"], ["data-contract-shards"])
        self.assertEqual(jobs["data-contract"]["if"], "always()")


if __name__ == "__main__":
    unittest.main()
