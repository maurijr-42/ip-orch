# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-04-21

### Added
- Created `ip_orch/core/worker.py` to decouple execution logic from `commands.py`.
- Added `pytest`, `pytest-mock`, and `ruff` to `[project.optional-dependencies]` in `pyproject.toml`.
- Added new automated tests to the `tests/` directory covering:
  - Configuration parsing (`config_store.py`)
  - CLI operations (`main.py` & `commands.py`)
  - Model Factory resolution logic (`model_factory.py`)

### Changed
- Refactored `cmd_run` inside `cli/commands.py` to execute the pre-built `worker.py` module rather than generating string-based execution scripts at runtime.
- Modified `ModelFactory` mapping to construct directories dynamically via the `--models-path` CLI parameter (or falling back to `~/.ip-orch/models`) instead of relying on heavily localized, hardcoded paths.
- Applied standard Type Hinting (`typing.Optional`, `typing.Dict`, `typing.Any`) and `Callable` definitions effectively across internal components.
- Adjusted broad `except Exception:` clauses to throw exceptions more specifically to improve overall API debugging capabilities.
- Enforced complete formatting and code quality checks through `ruff` across the `ip_orch` package.
