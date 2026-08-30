import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "services/api/src"))

from flow_api.fixtures.generator import (  # noqa: E402
    build_reference_package,
    write_canonical_package,
)
from flow_api.fixtures.known_answers import write_known_answers  # noqa: E402


def main() -> None:
    package = build_reference_package()
    write_canonical_package(package, REPOSITORY_ROOT / "fixtures/canonical")
    write_known_answers(package, REPOSITORY_ROOT / "fixtures/expected/known_answers.json")


if __name__ == "__main__":
    main()
