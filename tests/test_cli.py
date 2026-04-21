import argparse
from unittest.mock import patch, MagicMock

from ip_orch.cli.main import main
from ip_orch.cli.commands import cmd_add, cmd_models


@patch("ip_orch.cli.commands.add_model")
def test_cmd_add(mock_add_model):
    args = argparse.Namespace(env="myenv", model="mace-mp-0")
    assert cmd_add(args) == 0
    mock_add_model.assert_called_once_with("myenv", "mace-mp-0")


@patch("ip_orch.cli.commands.console.print")
def test_cmd_models(mock_print):
    args = argparse.Namespace(contains=None)
    with patch("ip_orch.cli.commands.load_config", return_value={"full_models": [["env1", "orb-v3"]]}):
        assert cmd_models(args) == 0
        # Should have built the table and printed
        assert mock_print.called


@patch("ip_orch.cli.main.cmd_add", return_value=0)
def test_main_routing(mock_cmd_add):
    # Main should route correctly
    assert main(["--add", "myenv", "mod"]) == 0
    mock_cmd_add.assert_called_once()
