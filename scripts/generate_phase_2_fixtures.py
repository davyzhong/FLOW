import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "services/api/src"))

from flow_api.fixtures.generator import (  # noqa: E402
    build_reference_package,
    write_canonical_package,
)


def main() -> None:
    write_canonical_package(build_reference_package(), REPOSITORY_ROOT / "fixtures/canonical")


if __name__ == "__main__":
    main()
