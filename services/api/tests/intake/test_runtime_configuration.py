from pathlib import Path

from flow_api.api.routes import intake

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]

def test_intake_configuration_root_is_resolved_from_runtime_layout(tmp_path: Path) -> None:
    contract = tmp_path / "templates/excel/flow_v1_contract.yaml"
    aliases = tmp_path / "config/intake/flow_v1_aliases.yaml"
    transforms = tmp_path / "config/intake/flow_v1_transforms.yaml"
    for path in (contract, aliases, transforms):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("test: true\n", encoding="utf-8")

    module_path = tmp_path / "src/flow_api/api/routes/intake.py"
    module_path.parent.mkdir(parents=True)
    module_path.touch()

    resolver = getattr(intake, "resolve_intake_configuration_root", None)
    assert resolver is not None, "runtime configuration must not depend on a fixed parent index"
    assert resolver(module_path) == tmp_path


def test_api_image_contains_intake_configuration_files() -> None:
    dockerfile = (REPOSITORY_ROOT / "infra/api.Dockerfile").read_text(encoding="utf-8")

    assert "COPY templates/excel/flow_v1_contract.yaml" in dockerfile
    assert "COPY config/intake" in dockerfile
