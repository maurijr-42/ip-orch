"""Public Python API for orchestrating IP-Orch runs."""

from __future__ import annotations

import argparse
import ast
import inspect
import os
import tempfile
import textwrap
import types
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from os import PathLike
from typing import Callable, Union

from .cli.commands import cmd_add, cmd_check_elements, cmd_configure, cmd_models, cmd_remove, cmd_run

PathValue = Union[str, PathLike[str]]
LogicFunction = Callable[[str, object], object]
ScriptOrFunction = Union[PathValue, LogicFunction]
Selection = Union[str, Iterable[str]]
_API_EXPORTS = {
    "IPOrch",
    "RunOptions",
    "add_model",
    "check_elements",
    "configure",
    "orchestrate",
    "remove_model",
    "run",
    "run_with_options",
    "supported_models",
}


@dataclass(frozen=True)
class RunOptions:
    """Options accepted by :func:`run`.

    This mirrors the CLI flags while accepting Python-native values such as
    lists or tuples for model/environment selections.
    """

    script: ScriptOrFunction
    envs: Selection | None = None
    models: Selection | None = None
    parallel: int = 1
    models_path: PathValue | None = None
    energy_linear_config: PathValue | None = None
    energy_linear_a: float | None = None
    energy_linear_b: float | None = None
    energy_linear_mode: str | None = None
    correction_elements: Selection | None = None
    no_energy_correction: bool = False
    reference_energy_source: str = "computed"


class IPOrch:
    """Python interface for the IP-Orch CLI commands."""

    def run(
        self,
        script: ScriptOrFunction,
        *,
        envs: Selection | None = None,
        models: Selection | None = None,
        parallel: int = 1,
        models_path: PathValue | None = None,
        energy_linear_config: PathValue | None = None,
        energy_linear_a: float | None = None,
        energy_linear_b: float | None = None,
        energy_linear_mode: str | None = None,
        correction_elements: Selection | None = None,
        no_energy_correction: bool = False,
        reference_energy_source: str = "computed",
        raise_on_error: bool = False,
    ) -> None:
        """Run a script path or Python logic function across selected models."""

        run(
            script,
            envs=envs,
            models=models,
            parallel=parallel,
            models_path=models_path,
            energy_linear_config=energy_linear_config,
            energy_linear_a=energy_linear_a,
            energy_linear_b=energy_linear_b,
            energy_linear_mode=energy_linear_mode,
            correction_elements=correction_elements,
            no_energy_correction=no_energy_correction,
            reference_energy_source=reference_energy_source,
            raise_on_error=raise_on_error,
        )

    def run_with_options(self, options: RunOptions, *, raise_on_error: bool = False) -> None:
        """Run IP-Orch with a :class:`RunOptions` instance."""

        run_with_options(options, raise_on_error=raise_on_error)

    def add_model(self, env: str, model: str) -> None:
        """Register an environment/model pair."""

        add_model(env, model)

    def remove_model(self, env: str, model: str | None = None) -> None:
        """Remove all models from an environment or one specific pair."""

        remove_model(env, model)

    def supported_models(self, contains: str | None = None) -> None:
        """Print known supported model aliases, optionally filtered by substring."""

        supported_models(contains)

    def check_elements(self, model: str, elements: Selection | None = None) -> None:
        """Check precomputed reference-energy support for a model."""

        check_elements(model, elements)

    def configure(self) -> None:
        """Run interactive environment discovery and setup."""

        configure()


def _selection_to_cli(value: Selection | None, *, option_name: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value

    try:
        items = [str(item).strip() for item in value if str(item).strip()]
    except TypeError as exc:
        raise TypeError(f"{option_name} must be a string or an iterable of strings") from exc

    return ",".join(items) if items else None


def run(
    script: ScriptOrFunction,
    *,
    envs: Selection | None = None,
    models: Selection | None = None,
    parallel: int = 1,
    models_path: PathValue | None = None,
    energy_linear_config: PathValue | None = None,
    energy_linear_a: float | None = None,
    energy_linear_b: float | None = None,
    energy_linear_mode: str | None = None,
    correction_elements: Selection | None = None,
    no_energy_correction: bool = False,
    reference_energy_source: str = "computed",
    raise_on_error: bool = False,
) -> int:
    """Run a Python script across configured MLIP environments/models.

    Parameters are equivalent to the ``ip-orch --run`` CLI flags, but selections
    may be provided as Python iterables:

    ``run("workflow.py", envs=["mace", "orb"])``
    ``run("workflow.py", models=["mace-mp", "orb-v3"], parallel=2)``

    Returns the same integer status code as the CLI. When ``raise_on_error`` is
    true, a non-zero status raises :class:`RuntimeError`.
    """

    options = RunOptions(
        script=script,
        envs=envs,
        models=models,
        parallel=parallel,
        models_path=models_path,
        energy_linear_config=energy_linear_config,
        energy_linear_a=energy_linear_a,
        energy_linear_b=energy_linear_b,
        energy_linear_mode=energy_linear_mode,
        correction_elements=correction_elements,
        no_energy_correction=no_energy_correction,
        reference_energy_source=reference_energy_source,
    )
    return run_with_options(options, raise_on_error=raise_on_error)


def run_with_options(options: RunOptions, *, raise_on_error: bool = False) -> int:
    """Run IP-Orch with a :class:`RunOptions` instance."""

    if options.envs and options.models:
        raise ValueError("Provide either envs or models, not both.")
    if not options.envs and not options.models:
        raise ValueError("Provide either envs or models.")
    parallel = int(options.parallel)
    if parallel < 1:
        raise ValueError("parallel must be at least 1.")

    with _script_path(options.script) as script_path:
        args = argparse.Namespace(
            script=script_path,
            envs=_selection_to_cli(options.envs, option_name="envs"),
            models=_selection_to_cli(options.models, option_name="models"),
            energy_linear_config=None if options.energy_linear_config is None else str(options.energy_linear_config),
            energy_linear_a=options.energy_linear_a,
            energy_linear_b=options.energy_linear_b,
            energy_linear_mode=options.energy_linear_mode,
            correction_elements=_selection_to_cli(options.correction_elements, option_name="correction_elements"),
            no_energy_correction=options.no_energy_correction,
            reference_energy_source=options.reference_energy_source,
            parallel=parallel,
            models_path=None if options.models_path is None else str(options.models_path),
        )

        status = cmd_run(args)
    if raise_on_error and status != 0:
        raise RuntimeError(f"IP-Orch run failed with exit code {status}.")
    return status


@contextmanager
def _script_path(script: ScriptOrFunction) -> Iterator[str]:
    if callable(script):
        source = _callable_script_source(script)
        with tempfile.TemporaryDirectory(prefix="iporch-") as tmpdir:
            path = os.path.join(tmpdir, "callable_logic.py")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(source)
            yield path
        return
    yield str(script)


def _callable_script_source(function: LogicFunction) -> str:
    if not inspect.isfunction(function):
        raise TypeError("script callables must be Python functions")
    if "<locals>" in function.__qualname__:
        raise ValueError("script callables must be top-level functions")

    filename = inspect.getsourcefile(function)
    if filename and os.path.exists(filename):
        with open(filename, encoding="utf-8") as handle:
            module_source = handle.read()
        return _module_callable_script_source(function, module_source, filename)

    try:
        function_source = textwrap.dedent(inspect.getsource(function)).rstrip()
    except (OSError, TypeError) as exc:
        raise ValueError(
            "script callable source could not be resolved. "
            "In notebooks, define the function in a normal code cell and avoid dynamically generated functions."
        ) from exc

    parts = _inferred_global_segments(function)
    parts.append(function_source)
    parts.append("")
    parts.append("def main(calculator_name, ase_calculator):")
    parts.append(f"    return {function.__name__}(calculator_name, ase_calculator)")
    parts.append("")
    return "\n\n".join(parts)


def _module_callable_script_source(function: LogicFunction, module_source: str, filename: str) -> str:
    tree = ast.parse(module_source, filename=filename)
    selected_segments = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "ip_orch":
            names = [alias for alias in node.names if alias.name not in _API_EXPORTS]
            if names:
                selected_segments.append(_format_import_from("ip_orch", names))
        elif isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef)):
            segment = ast.get_source_segment(module_source, node)
            if segment:
                selected_segments.append(textwrap.dedent(segment).rstrip())
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            if not _contains_api_call(node):
                segment = ast.get_source_segment(module_source, node)
                if segment:
                    selected_segments.append(textwrap.dedent(segment).rstrip())

    selected_segments.append("")
    selected_segments.append("def main(calculator_name, ase_calculator):")
    selected_segments.append(f"    return {function.__name__}(calculator_name, ase_calculator)")
    selected_segments.append("")
    return "\n\n".join(selected_segments)


def _inferred_global_segments(function: LogicFunction) -> list[str]:
    segments = []
    seen = set()
    globals_dict = function.__globals__
    for name in function.__code__.co_names:
        if name in seen or name not in globals_dict or name in _API_EXPORTS:
            continue
        seen.add(name)
        value = globals_dict[name]
        segment = _global_segment(name, value)
        if segment:
            segments.append(segment)
    return segments


def _global_segment(name: str, value: object) -> str | None:
    if isinstance(value, types.ModuleType):
        module_name = getattr(value, "__name__", "")
        if not module_name:
            return None
        return f"import {module_name} as {name}" if module_name != name else f"import {module_name}"

    module_name = getattr(value, "__module__", None)
    object_name = getattr(value, "__name__", None)
    if module_name and object_name and module_name != "__main__":
        if object_name == name:
            return f"from {module_name} import {object_name}"
        return f"from {module_name} import {object_name} as {name}"

    if isinstance(value, (str, int, float, bool, type(None), tuple, list, dict, set)):
        return f"{name} = {value!r}"

    return None


def _contains_api_call(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name) and func.id in _API_EXPORTS:
                return True
            if isinstance(func, ast.Attribute) and func.attr in _API_EXPORTS:
                return True
    return False


def _format_import_from(module: str, aliases: list[ast.alias]) -> str:
    parts = []
    for alias in aliases:
        if alias.asname:
            parts.append(f"{alias.name} as {alias.asname}")
        else:
            parts.append(alias.name)
    return f"from {module} import {', '.join(parts)}"


def add_model(env: str, model: str) -> int:
    """Register an environment/model pair."""

    return cmd_add(argparse.Namespace(env=env, model=model))


def remove_model(env: str, model: str | None = None) -> int:
    """Remove all models from an environment or one specific pair."""

    return cmd_remove(argparse.Namespace(env=env, model=model))


def supported_models(contains: str | None = None) -> int:
    """Print known supported model aliases, optionally filtered by substring."""

    return cmd_models(argparse.Namespace(contains=contains))


def check_elements(model: str, elements: Selection | None = None) -> int:
    """Check precomputed reference-energy support for a model."""

    return cmd_check_elements(
        argparse.Namespace(model=model, elements=_selection_to_cli(elements, option_name="elements"))
    )


def configure() -> int:
    """Run interactive environment discovery and setup."""

    return cmd_configure(argparse.Namespace())


orchestrate = run
