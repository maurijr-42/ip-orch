from pathlib import Path
from unittest.mock import patch

import pytest
from ase.build import bulk

from ip_orch import (
    IPOrch,
    RunOptions,
    orchestrate,
    run,
    run_with_options,
)


def callable_logic(calculator_name, ase_calculator):
    return calculator_name, ase_calculator


LATTICE_A = 3.6


def notebook_style_logic(calculator_name, ase_calculator):
    atoms = bulk("Cu", "fcc", a=LATTICE_A)
    atoms.calc = ase_calculator
    return calculator_name


@patch("ip_orch.api.cmd_run", return_value=0)
def test_run_accepts_python_native_model_selection(mock_cmd_run):
    """Expose orchestration through Python without requiring CLI argument strings."""

    assert run(Path("script.py"), models=["mace-mp", "orb-v3"], parallel=2, correction_elements=["C", "Cu"]) == 0

    args = mock_cmd_run.call_args.args[0]
    assert args.script == "script.py"
    assert args.models == "mace-mp,orb-v3"
    assert args.envs is None
    assert args.parallel == 2
    assert args.correction_elements == "C,Cu"


@patch("ip_orch.api.cmd_run")
def test_run_accepts_logic_function(mock_cmd_run):
    """Materialize a Python callable as the worker script run by IP-Orch."""

    captured = {}

    def fake_cmd_run(args):
        captured["script"] = Path(args.script)
        captured["source"] = captured["script"].read_text(encoding="utf-8")
        return 0

    mock_cmd_run.side_effect = fake_cmd_run

    assert run(callable_logic, models=["mace-mp"]) == 0

    assert captured["script"].name == "callable_logic.py"
    assert not any(line.startswith("from ip_orch import") for line in captured["source"].splitlines())
    assert "def callable_logic(calculator_name, ase_calculator):" in captured["source"]
    assert "def main(calculator_name, ase_calculator):" in captured["source"]
    assert "return callable_logic(calculator_name, ase_calculator)" in captured["source"]


@patch("ip_orch.api.inspect.getsource")
@patch("ip_orch.api.inspect.getsourcefile", return_value="/tmp/ipykernel_1/123.py")
@patch("ip_orch.api.cmd_run")
def test_run_accepts_notebook_function_without_real_source_file(
    mock_cmd_run,
    mock_getsourcefile,
    mock_getsource,
):
    """Use inspect.getsource when notebook source paths do not exist on disk."""

    mock_getsource.return_value = """
def notebook_style_logic(calculator_name, ase_calculator):
    atoms = bulk("Cu", "fcc", a=LATTICE_A)
    atoms.calc = ase_calculator
    return calculator_name
"""
    captured = {}

    def fake_cmd_run(args):
        captured["source"] = Path(args.script).read_text(encoding="utf-8")
        return 0

    mock_cmd_run.side_effect = fake_cmd_run

    assert run(notebook_style_logic, models=["mace-mp"]) == 0

    assert "from ase.build.bulk import bulk" in captured["source"]
    assert "LATTICE_A = 3.6" in captured["source"]
    assert "def notebook_style_logic(calculator_name, ase_calculator):" in captured["source"]
    assert "return notebook_style_logic(calculator_name, ase_calculator)" in captured["source"]


@patch("ip_orch.api.cmd_run", return_value=0)
def test_run_with_options_forwards_cli_equivalent_fields(mock_cmd_run):
    """Allow callers to group run configuration in a dataclass."""

    options = RunOptions(
        script="workflow.py",
        envs=("mace", "orb"),
        models_path=Path("/models"),
        energy_linear_a=1.0,
        energy_linear_b=-0.1,
        energy_linear_mode="per_atom",
        reference_energy_source="precomputed",
    )

    assert run_with_options(options) == 0

    args = mock_cmd_run.call_args.args[0]
    assert args.envs == "mace,orb"
    assert args.models_path == "/models"
    assert args.energy_linear_a == 1.0
    assert args.energy_linear_b == -0.1
    assert args.energy_linear_mode == "per_atom"
    assert args.reference_energy_source == "precomputed"


@patch("ip_orch.api.cmd_run", return_value=2)
def test_run_can_raise_on_nonzero_status(mock_cmd_run):
    """Optionally convert CLI-style status codes into Python exceptions."""

    with pytest.raises(RuntimeError, match="exit code 2"):
        run("script.py", envs="mace", raise_on_error=True)


def test_run_rejects_missing_or_ambiguous_selection():
    """Require exactly one run selection mechanism."""

    with pytest.raises(ValueError, match="either envs or models"):
        run("script.py")
    with pytest.raises(ValueError, match="not both"):
        run("script.py", envs=["mace"], models=["mace-mp"])
    with pytest.raises(ValueError, match="parallel"):
        run("script.py", envs=["mace"], parallel=0)


@patch("ip_orch.api.cmd_run", return_value=0)
def test_orchestrate_alias(mock_cmd_run):
    """Provide a descriptive alias for script callers."""

    assert orchestrate("script.py", envs=["mace"]) == 0
    assert mock_cmd_run.call_args.args[0].envs == "mace"


@patch("ip_orch.api.cmd_add", return_value=0)
def test_class_add_model_method(mock_cmd_add):
    """Expose --add as a class method."""

    orch = IPOrch()
    assert orch.add_model("mace", "mace-mp") is None
    args = mock_cmd_add.call_args.args[0]
    assert args.env == "mace"
    assert args.model == "mace-mp"


@patch("ip_orch.api.cmd_remove", return_value=0)
def test_class_remove_model_method(mock_cmd_remove):
    """Expose --remove as a class method."""

    orch = IPOrch()
    assert orch.remove_model("mace", "mace-mp") is None
    args = mock_cmd_remove.call_args.args[0]
    assert args.env == "mace"
    assert args.model == "mace-mp"


@patch("ip_orch.api.cmd_models", return_value=0)
def test_class_supported_models_method(mock_cmd_models):
    """Expose --supported-models as a class method."""

    orch = IPOrch()
    assert orch.supported_models("mace") is None
    assert mock_cmd_models.call_args.args[0].contains == "mace"


@patch("ip_orch.api.cmd_check_elements", return_value=0)
def test_class_check_elements_method(mock_cmd_check_elements):
    """Expose --check-elements as a class method."""

    orch = IPOrch()
    assert orch.check_elements("mace-mp", ["C", "Cu"]) is None
    args = mock_cmd_check_elements.call_args.args[0]
    assert args.model == "mace-mp"
    assert args.elements == "C,Cu"


@patch("ip_orch.api.cmd_configure", return_value=0)
def test_class_configure_method(mock_cmd_configure):
    """Expose --configure as a class method."""

    orch = IPOrch()
    assert orch.configure() is None
    mock_cmd_configure.assert_called_once()


@patch("ip_orch.api.cmd_run", return_value=0)
def test_class_run_method(mock_cmd_run):
    """Expose --run as a class method."""

    orch = IPOrch()
    assert orch.run("script.py", envs=["mace"]) is None
    args = mock_cmd_run.call_args.args[0]
    assert args.script == "script.py"
    assert args.envs == "mace"
