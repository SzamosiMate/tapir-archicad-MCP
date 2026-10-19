"""Generator metadata must match the dependency and installed model contracts."""

import importlib.util
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "mcp_generator_config", Path(__file__).resolve().parents[2] / "scripts" / "generator_config.py"
)
config = importlib.util.module_from_spec(SPEC)
# dataclasses resolves annotations through the defining module.
sys.modules[SPEC.name] = config
SPEC.loader.exec_module(config)


def project_file(tmp_path, dependency):
    path = tmp_path / "pyproject.toml"
    path.write_text(f'[project]\ndependencies = ["{dependency}"]\n', encoding="utf-8")
    return path


def test_metadata_sources_match_the_pinned_model_version():
    urls = [config.ORGANIZED_COMMANDS_URL, config.TAPIR_CONFIG.model_names_url, config.OFFICIAL_CONFIG.model_names_url]
    assert all(f"/refs/tags/v{config.MULTICONN_VERSION}/" in url for url in urls)
    assert config.version("multiconn-archicad") == config.MULTICONN_VERSION


def test_updating_dependency_changes_the_source_version(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "version", lambda name: "9.8.7")
    assert config.get_multiconn_version(project_file(tmp_path, "multiconn-archicad==9.8.7")) == "9.8.7"


def test_mismatched_installed_models_fail_before_generation(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "version", lambda name: "0.9.3")
    with pytest.raises(RuntimeError, match="uv sync --locked"):
        config.get_multiconn_version(project_file(tmp_path, "multiconn-archicad==0.9.4"))


@pytest.mark.parametrize("dependency", ["multiconn-archicad>=0.9.4", "multiconn-archicad==0.9.*"])
def test_floating_dependencies_cannot_select_generator_metadata(tmp_path, dependency):
    with pytest.raises(ValueError, match="exact"):
        config.get_multiconn_version(project_file(tmp_path, dependency))
