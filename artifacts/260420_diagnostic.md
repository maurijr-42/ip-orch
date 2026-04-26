# IP-Orch Diagnostic

## Summary

**IP-Orch** is a CLI-driven Python package for orchestrating Machine Learning Interatomic Potentials (MLIPs). It enables running a single ASE-based script across multiple MLIP environments (typically separate Conda envs), with optional energy correction (linear scaling + element-reference shift). It supports ~20+ models (MACE, ORB, GRACE, NequIP, SevenNet, CHGNet, etc.) via a factory pattern.

**Architecture**:

- `ip_orch/core/` — `ModelFactory` (creates ASE calculators), `energy_correction` (wrapper calculators), `worker.py` (subprocess entry point)
- `ip_orch/cli/` — argparse CLI with `--add`, `--remove`, `--run`, `--configure`, `--supported-models`
- `ip_orch/config/` — JSON config store at `~/.ip-orch/config.json` for (env, model) pairs
- **Execution model**: CLI dispatches `worker.py` into each Conda env via `conda run` or direct Python path; the worker instantiates the calculator, applies corrections, and calls the user script

---

## Suggested Improvements

### High Priority

1. **Refactor `ModelFactory` — monolithic if-chain is unmaintainable** (`model_factory.py:78-285`)
   - Replace the 200-line if-elif chain with a **registry pattern**: dict of `{key: callable}` or use `entry_points` for plugins. Adding a model should not require editing the factory class.
   - Each model's instantiation logic could live in its own module/function.

2. **Add `ase` to dependencies** — The package fundamentally requires ASE (`energy_correction.py` imports it unconditionally, `worker.py` uses it), but `ase` is not in `pyproject.toml`.

3. **Fix `requires-python` inconsistency** — States `>=3.8` but uses `dict[str, float]` (3.9+ only syntax in `energy_correction.py:70`).

4. **Fix hardcoded repo root** (`commands.py:157`) — Computes repo root relative to `__file__`, which breaks when pip-installed. Use `importlib.resources` or `__package__` instead.

5. **`worker.py` positional argv parsing is fragile** (`worker.py:19-30`) — 11+ positional CLI args parsed manually. Replace with JSON payload via stdin or a single `--payload` JSON arg.

### Medium Priority

6. **Add subcommands instead of mutually exclusive flags** — `ip-orch add`, `ip-orch run`, `ip-orch configure` is more idiomatic than `ip-orch --add`, `ip-orch --run`, etc. Would also allow composing flags.

7. **Expose a public Python API** — `core/__init__.py` is empty. Users should be able to `from ip_orch import ModelFactory, apply_linear_correction` programmatically, not just via CLI.

8. **Add structured output for `--run`** — No results aggregation (CSV/JSON). Just stdout. For benchmarking, structured output is essential.

9. **Add parallel execution** — Models run sequentially in `cmd_run`. Support `--parallel N` or async execution for benchmarks.

10. **No CI/CD** — No GitHub Actions for testing, linting, or publishing. The `to-do` file mentions this.

11. **`repo_url_for_alias` has fragile matching** (`repo_map.py:20-52`) — String containment checks like `"nequip" in a` would match `nequix` incorrectly. Use prefix/exact matching.

12. **Replace `print()` with `logging`** — No structured logging anywhere; all output is via `print()` or `rich` directly.

13. **Add `__all__` and type-checking** — No explicit public API, no `mypy`/`pyright` in dev deps or CI.

### Lower Priority

14. **Dynamic versioning** — Hardcoded `0.0.1` in `pyproject.toml`. Use `dynamic = ["version"]` with `setuptools_scm` or a `__version__` attr.

15. **Add optional dependency groups** — `[mace]`, `[orb]`, `[all]` extras for model-specific packages.

16. **Test coverage is thin** — `worker.py` (most complex module) and `cmd_run` (most critical CLI path) have zero tests. Model factory tests only cover 2 of ~20 models.

17. **Cache element energies** — Preflight recomputes every run. Persist in config store.

18. **Add `--dry-run` flag** — Preview which models would run without executing.

19. **Add `CHANGELOG.md`** — No version history.

20. **Energy correction wrappers** — Each call creates a new inner class. Consider a single parameterized wrapper class or ASE's built-in calculator composition.
