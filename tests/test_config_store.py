from unittest.mock import patch
import json
import pytest

from ip_orch.config import config_store

@pytest.fixture
def mock_config_dir(tmp_path):
    config_path = tmp_path / "config.json"
    with patch("ip_orch.config.config_store.CONFIG_DIR", str(tmp_path)), \
         patch("ip_orch.config.config_store.CONFIG_PATH", str(config_path)):
        yield config_path


def test_load_default_config(mock_config_dir):
    cfg = config_store.load_config()
    assert cfg["base_env"] == "base"
    assert cfg["models_path"] == ""
    assert isinstance(cfg["full_models"], list)


def test_add_model(mock_config_dir):
    config_store.add_model("mace", "mace-mp-0")
    cfg = config_store.load_config()
    assert ["mace", "mace-mp-0"] in cfg["full_models"]
    
    # Adding again shouldn't duplicate
    config_store.add_model("mace", "mace-mp-0")
    cfg = config_store.load_config()
    assert cfg["full_models"].count(["mace", "mace-mp-0"]) == 1


def test_remove_model(mock_config_dir):
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
    config_store.set_base_env("myenv")
    assert config_store.load_config()["base_env"] == "myenv"
    
    config_store.set_models_path("/new/path")
    assert config_store.load_config()["models_path"] == "/new/path"


def test_model_status(mock_config_dir):
    config_store.set_model_status("mace", "ok")
    assert config_store.get_model_status_map() == {"mace": "ok"}
    
    config_store.set_model_status("orb", "broken")
    assert config_store.get_model_status_map() == {"mace": "ok", "orb": "broken"}
    
    # Invliad status
    config_store.set_model_status("orb", "unknown")
    assert config_store.get_model_status_map()["orb"] == "broken"
