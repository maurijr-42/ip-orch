import json
from unittest.mock import patch

import pytest

from ip_orch.config import config_store


@pytest.fixture
def mock_config_dir(tmp_path):
    """Route config reads/writes to a temporary test directory."""

    config_path = tmp_path / "config.json"
    with (
        patch("ip_orch.config.config_store.CONFIG_DIR", str(tmp_path)),
        patch("ip_orch.config.config_store.CONFIG_PATH", str(config_path)),
    ):
        yield config_path


def test_load_default_config(mock_config_dir):
    """Return default configuration when no user config file exists."""

    cfg = config_store.load_config()
    assert cfg["base_env"] == "base"
    assert cfg["models_path"] == ""
    assert isinstance(cfg["full_models"], list)


def test_load_config_recovers_from_invalid_json(mock_config_dir):
    """Ignore a corrupted config file and fall back to safe defaults."""

    mock_config_dir.write_text("{not valid json", encoding="utf-8")

    assert config_store.load_config() == config_store.DEFAULT_CONFIG


def test_load_config_normalizes_wrong_collection_types(mock_config_dir):
    """Repair config fields whose persisted types do not match the expected schema."""

    mock_config_dir.write_text(
        json.dumps({"full_models": "not-a-list", "model_status": ["not", "a", "dict"]}),
        encoding="utf-8",
    )

    cfg = config_store.load_config()
    assert cfg["full_models"] == []
    assert cfg["model_status"] == {}


def test_add_model(mock_config_dir):
    """Append a new env/model pair once and avoid duplicate entries."""

    config_store.add_model("mace", "mace-mp-0")
    cfg = config_store.load_config()
    assert ["mace", "mace-mp-0"] in cfg["full_models"]

    # Adding again shouldn't duplicate
    config_store.add_model("mace", "mace-mp-0")
    cfg = config_store.load_config()
    assert cfg["full_models"].count(["mace", "mace-mp-0"]) == 1


def test_remove_model(mock_config_dir):
    """Remove either one model from an env or all models for that env."""

    config_store.add_model("mace", "mace-mp-0")
    config_store.add_model("mace", "mace-mp-1")
    config_store.add_model("orb", "orb-v3")

    assert config_store.remove_model("mace", "mace-mp-0") is True
    cfg = config_store.load_config()
    assert ["mace", "mace-mp-0"] not in cfg["full_models"]
    assert ["mace", "mace-mp-1"] in cfg["full_models"]
    assert ["orb", "orb-v3"] in cfg["full_models"]

    # Remove by env only
    assert config_store.remove_model("mace") is True
    cfg = config_store.load_config()
    assert ["mace", "mace-mp-1"] not in cfg["full_models"]


def test_set_properties(mock_config_dir):
    """Persist base environment and model path settings."""

    config_store.set_base_env("myenv")
    assert config_store.load_config()["base_env"] == "myenv"

    config_store.set_models_path("/new/path")
    assert config_store.load_config()["models_path"] == "/new/path"


def test_model_status(mock_config_dir):
    """Persist only accepted model status values."""

    config_store.set_model_status("mace", "ok")
    assert config_store.get_model_status_map() == {"mace": "ok"}

    config_store.set_model_status("orb", "broken")
    assert config_store.get_model_status_map() == {"mace": "ok", "orb": "broken"}

    # Invalid status
    config_store.set_model_status("orb", "unknown")
    assert config_store.get_model_status_map()["orb"] == "broken"
