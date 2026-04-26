import os
from unittest.mock import patch

from ip_orch.cli.env_utils import (
    _current_conda_env,
    _discover_conda_envs,
    _discover_envs_from_dir,
    _match_known_token,
    _python_for_env,
)


def test_discover_conda_envs_parses_conda_env_list_output():
    """Parse `conda env list` output while ignoring comment/header lines."""

    output = """
# conda environments:
base                  *  /opt/miniconda3
mace                     /opt/miniconda3/envs/mace
orb                      /opt/miniconda3/envs/orb
"""
    with patch("ip_orch.cli.env_utils.subprocess.check_output", return_value=output):
        assert _discover_conda_envs() == {"base", "mace", "orb"}


def test_discover_conda_envs_returns_empty_set_when_conda_is_unavailable():
    """Treat missing conda as a non-fatal discovery miss."""

    with patch("ip_orch.cli.env_utils.subprocess.check_output", side_effect=FileNotFoundError):
        assert _discover_conda_envs() == set()


def test_discover_envs_from_dir_finds_directories_with_python(tmp_path):
    """Find local MLIP environments by looking for executable Python binaries."""

    env_dir = tmp_path / "envs"
    python_bin = env_dir / "mace" / "bin" / "python"
    python_bin.parent.mkdir(parents=True)
    python_bin.write_text("#!/usr/bin/env python\n", encoding="utf-8")
    python_bin.chmod(0o755)
    (env_dir / "not_an_env").mkdir()

    assert _discover_envs_from_dir(str(env_dir)) == {"mace"}


def test_python_for_env_checks_visible_and_hidden_env_directories(tmp_path):
    """Resolve the Python executable for both env and .env directory layouts."""

    hidden_python = tmp_path / ".orb" / "bin" / "python"
    hidden_python.parent.mkdir(parents=True)
    hidden_python.write_text("#!/usr/bin/env python\n", encoding="utf-8")
    hidden_python.chmod(0o755)

    assert _python_for_env("orb", str(tmp_path)) == str(hidden_python)


def test_match_known_token_detects_model_family_from_env_name():
    """Infer default model family suggestions from environment names."""

    assert _match_known_token("mlip-orb-v3") == "orb"
    assert _match_known_token("custom-env") == ""


def test_current_conda_env_prefers_conda_default_env_over_prefix_basename():
    """Use CONDA_DEFAULT_ENV when present and fall back to CONDA_PREFIX basename."""

    with patch.dict(os.environ, {"CONDA_DEFAULT_ENV": "active", "CONDA_PREFIX": "/tmp/other"}, clear=True):
        assert _current_conda_env() == "active"

    with patch.dict(os.environ, {"CONDA_PREFIX": "/tmp/from-prefix"}, clear=True):
        assert _current_conda_env() == "from-prefix"
