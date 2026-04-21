# IP-Orch Improvements Plan

This document outlines the proposed changes to the `ip-orch` codebase, driven by Python best practices and the [Karpathy Guidelines](https://x.com/karpathy/status/2015883857489522876) (Simplicity First, Think Before Coding, Surgical Changes).

## User Review Required

> [!IMPORTANT]
> The proposed architecture will refactor how the inner worker script executes and how the `ModelFactory` resolves MLIP weights. Since this touches the core invocation logic, please review to ensure it aligns with your usage of Conda environments and local predefined models.

## Proposed Changes

---

### CLI & Execution Module

Currently, `ip_orch/cli/commands.py` contains a `_generate_worker()` function that writes over 100 lines of Python code as a raw string to a temporary file before execution.

- **Problem:** String-based code generation is brittle, impossible to lint, hard to debug, and violates the **Simplicity First** rule.
- **Suggestion:** Extract this logic into a dedicated, standard Python module (e.g., `ip_orch/core/worker.py`). The CLI can simply invoke it using `python -m ip_orch.core.worker [args...]` or pointing directly to the module file.

#### [NEW] `ip_orch/core/worker.py`
Create a new file containing the execution logic extracted from the `_generate_worker()` string template.

#### [MODIFY] `ip_orch/cli/commands.py`
Remove `_generate_worker()` and update `cmd_run()` to invoke the new `worker.py` script path or module using `subprocess.run()`.

---

### Core Factory & Model Management

Currently, `ip_orch/core/model_factory.py` consists of a monolithic `if/elif` block checking string keys, with widespread usage of hardcoded, user-specific paths (e.g., `/home/p.zanineli/pretrained/...`) and sweeping `except Exception` blocks that hide underlying errors.

- **Problem:** Hardcoded paths break portability. Masking exceptions directly violates the **Think Before Coding: Don't hide confusion** guideline.
- **Suggestion:** Refactor `ModelFactory` to dynamically build paths from the `models_path` config parameter (or environment variables), eliminating hardcoded user directories. Remove broad `except Exception` clauses so that relevant import or file missing errors are explicitly raised to the user.

#### [MODIFY] `ip_orch/core/model_factory.py`
- Replace `/home/p.zanineli/...` with `os.path.join(models_path, ...)` or a configurable system.
- Convert the giant conditional block into a cleaner "registry" pattern or modular mapping if feasible, but at minimum, clean up the instantiation logic.
- Remove generic `except Exception` blocks in the dynamic imports (like in ORB V2) and catch specifically `ImportError`, bubbling up initialization errors appropriately.

---

### Types and Code Style

- **Problem:** Many functions, primarily in `model_factory.py` and `commands.py`, lack strict type annotations and docstrings for parameters.
- **Suggestion:** Apply modern Python typing strictly (e.g. ensuring `Calculator` return types are explicit).

## Open Questions

> [!WARNING]
> - **Model Paths:** What is the preferred method for users to specify custom paths to `.pt/.pth` model files when removing the hardcoded `/home/p.zanineli/` directory? Should we rely completely on the `--models-path` CLI parameter? 
> - **Preflight Output:** `commands.py` catches `sys.exit` code from the worker. Do you want more granular logging capabilities moving forward?

## Verification Plan

### Automated Tests
- Since the package has a `tests/` directory, I will execute `pytest` (if available) before and after changes to verify no functionality is broken.
- Verify that `ip-orch --help` and `ip-orch --supported-models` behave exactly as they did before.

### Manual Verification
- Simulate a run by calling the refactored `worker.py` with mock environments and arguments to ensure the arguments parse cleanly, mimicking what `cmd_run` dispatches.
