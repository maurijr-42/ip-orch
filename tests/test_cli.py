import argparse
import os
import subprocess
from unittest.mock import patch

from ip_orch.cli.main import main
from ip_orch.cli.commands import _package_parent_path, _worker_resource_path, cmd_add, cmd_models, cmd_run


@patch("ip_orch.cli.commands.add_model")
def test_cmd_add(mock_add_model):
    """Route --add data to the config layer and return success."""

    args = argparse.Namespace(env="myenv", model="mace-mp-0")
    assert cmd_add(args) == 0
    mock_add_model.assert_called_once_with("myenv", "mace-mp-0")


@patch("ip_orch.cli.commands.console.print")
def test_cmd_models(mock_print):
    """Render the supported-models table using configured aliases first."""

    args = argparse.Namespace(contains=None)
    with patch("ip_orch.cli.commands.load_config", return_value={"full_models": [["env1", "orb-v3"]]}):
        assert cmd_models(args) == 0
        # Should have built the table and printed
        assert mock_print.called


@patch("ip_orch.cli.main.cmd_add", return_value=0)
def test_main_routing(mock_cmd_add):
    """Dispatch the top-level --add command to cmd_add."""

    # Main should route correctly
    assert main(["--add", "myenv", "mod"]) == 0
    mock_cmd_add.assert_called_once()


@patch("ip_orch.cli.main.cmd_run", return_value=0)
def test_main_forwards_parallel(mock_cmd_run):
    """Parse --parallel and forward it to cmd_run."""

    assert main(["--run", "script.py", "--models", "orb-v3", "--parallel", "3"]) == 0

    args = mock_cmd_run.call_args.args[0]
    assert args.parallel == 3


@patch("ip_orch.cli.commands.console.print")
@patch("ip_orch.cli.commands.set_model_status")
@patch("ip_orch.cli.commands._python_for_env", return_value="/env/python")
@patch("ip_orch.cli.commands._worker_resource_path", return_value="/pkg/worker.py")
@patch("ip_orch.cli.commands._package_parent_path", return_value="/pkg")
@patch("ip_orch.cli.commands.load_config")
@patch("ip_orch.cli.commands._run_subprocess")
def test_cmd_run_parallel_executes_all_models(
    mock_run_subprocess,
    mock_load_config,
    mock_package_parent_path,
    mock_worker_resource_path,
    mock_python_for_env,
    mock_set_model_status,
    mock_print,
):
    """Run all selected models with captured output when --parallel is greater than one."""

    mock_load_config.return_value = {
        "full_models": [["env1", "orb-v3"], ["env2", "mace-mp"]],
        "models_path": "/models",
        "envs_base_dir": "/envs",
    }
    mock_run_subprocess.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok\n", stderr="")
    args = argparse.Namespace(
        script="script.py",
        envs=None,
        models="orb-v3,mace-mp",
        energy_linear_config=None,
        energy_linear_a=None,
        energy_linear_b=None,
        energy_linear_mode=None,
        correction_elements=None,
        no_energy_correction=False,
        parallel=2,
    )

    assert cmd_run(args) == 0

    assert mock_run_subprocess.call_count == 2
    assert mock_set_model_status.call_count == 2


@patch("ip_orch.cli.commands.console.print")
@patch("ip_orch.cli.commands.set_model_status")
@patch("ip_orch.cli.commands._python_for_env", return_value="/env/python")
@patch("ip_orch.cli.commands._worker_resource_path", return_value="/pkg/worker.py")
@patch("ip_orch.cli.commands._package_parent_path", return_value="/pkg")
@patch("ip_orch.cli.commands.load_config")
@patch("ip_orch.cli.commands._run_subprocess")
def test_cmd_run_sequential_uses_streaming_subprocess_output(
    mock_run_subprocess,
    mock_load_config,
    mock_package_parent_path,
    mock_worker_resource_path,
    mock_python_for_env,
    mock_set_model_status,
    mock_print,
):
    """Run one selected model at a time with live subprocess output by default."""

    mock_load_config.return_value = {
        "full_models": [["env1", "orb-v3"]],
        "models_path": "/models",
        "envs_base_dir": "/envs",
    }
    mock_run_subprocess.return_value = subprocess.CompletedProcess(args=[], returncode=0)
    args = argparse.Namespace(
        script="script.py",
        envs="env1",
        models=None,
        energy_linear_config=None,
        energy_linear_a=None,
        energy_linear_b=None,
        energy_linear_mode=None,
        correction_elements=None,
        no_energy_correction=False,
        parallel=1,
    )

    assert cmd_run(args) == 0

    mock_run_subprocess.assert_called_once()
    assert mock_run_subprocess.call_args.kwargs["capture_output"] is False
    mock_set_model_status.assert_called_once_with("orb-v3", "ok")


@patch("ip_orch.cli.commands.console.print")
@patch("ip_orch.cli.commands.set_model_status")
@patch("ip_orch.cli.commands._python_for_env", return_value="/env/python")
@patch("ip_orch.cli.commands._worker_resource_path", return_value="/pkg/worker.py")
@patch("ip_orch.cli.commands._package_parent_path", return_value="/pkg")
@patch("ip_orch.cli.commands.load_config")
@patch("ip_orch.cli.commands._run_subprocess")
def test_cmd_run_preflight_failure_marks_model_broken(
    mock_run_subprocess,
    mock_load_config,
    mock_package_parent_path,
    mock_worker_resource_path,
    mock_python_for_env,
    mock_set_model_status,
    mock_print,
):
    """Stop execution and mark a model broken when element-energy preflight fails."""

    mock_load_config.return_value = {
        "full_models": [["env1", "orb-v3"]],
        "models_path": "/models",
        "envs_base_dir": "/envs",
    }
    mock_run_subprocess.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=9,
        stdout="",
        stderr="preflight failed",
    )
    args = argparse.Namespace(
        script="script.py",
        envs="env1",
        models=None,
        energy_linear_config=None,
        energy_linear_a=None,
        energy_linear_b=None,
        energy_linear_mode=None,
        correction_elements="C",
        no_energy_correction=False,
        parallel=1,
    )

    assert cmd_run(args) == 2

    mock_set_model_status.assert_called_once_with("orb-v3", "broken")


@patch("ip_orch.cli.commands.console.print")
@patch("ip_orch.cli.commands.set_model_status")
@patch("ip_orch.cli.commands._python_for_env", return_value="/env/python")
@patch("ip_orch.cli.commands._worker_resource_path", return_value="/pkg/worker.py")
@patch("ip_orch.cli.commands._package_parent_path", return_value="/pkg")
@patch("ip_orch.cli.commands.load_config")
@patch("ip_orch.cli.commands._run_subprocess")
def test_cmd_run_parallel_summary_includes_parallel_notice(
    mock_run_subprocess,
    mock_load_config,
    mock_package_parent_path,
    mock_worker_resource_path,
    mock_python_for_env,
    mock_set_model_status,
    mock_print,
):
    """Show the parallel execution notice in the initial model summary panel."""

    mock_load_config.return_value = {
        "full_models": [["env1", "orb-v3"], ["env2", "mace-mp"]],
        "models_path": "/models",
        "envs_base_dir": "/envs",
    }
    mock_run_subprocess.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    args = argparse.Namespace(
        script="script.py",
        envs=None,
        models="orb-v3,mace-mp",
        energy_linear_config=None,
        energy_linear_a=None,
        energy_linear_b=None,
        energy_linear_mode=None,
        correction_elements=None,
        no_energy_correction=False,
        parallel=2,
    )

    assert cmd_run(args) == 0

    first_panel = mock_print.call_args_list[0].args[0]
    assert "IP-Orch: starting execution | running up to 2 models in parallel" in first_panel.renderable


def test_worker_resource_path():
    """Resolve package resource paths used to invoke the worker script."""

    assert _worker_resource_path().endswith(os.path.join("ip_orch", "core", "worker.py"))
    assert _package_parent_path()
