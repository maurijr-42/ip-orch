"""
Worker script executed inside standard or external environment
to load a user script and provide it with an instantiated ASE calculator.
"""

import importlib.util
import inspect
import json
import logging
import os
import sys
import warnings
from typing import Dict, Optional

warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)


def main() -> None:
    try:
        user_script_path = sys.argv[1]
        calculator_name_arg = sys.argv[2]
        model_name_arg = sys.argv[3]
        models_path_arg = sys.argv[4] if len(sys.argv) > 4 else ""
        repo_root_arg = sys.argv[5] if len(sys.argv) > 5 else ""

        linear_a_arg = sys.argv[6] if len(sys.argv) > 6 else ""
        linear_b_arg = sys.argv[7] if len(sys.argv) > 7 else ""
        linear_mode_arg = sys.argv[8] if len(sys.argv) > 8 else "total_energy"
        elements_arg = sys.argv[9] if len(sys.argv) > 9 else ""
        element_energies_json_arg = sys.argv[10] if len(sys.argv) > 10 else ""
        preflight_arg = sys.argv[11] if len(sys.argv) > 11 else ""

        def _to_float(s: str) -> Optional[float]:
            s = (s or "").strip()
            return float(s) if s else None

        linear_a = _to_float(linear_a_arg)
        linear_b = _to_float(linear_b_arg)
        linear_mode = (linear_mode_arg or "total_energy").strip() or "total_energy"

        elements_raw = (elements_arg or "").strip()
        elements = [e.strip() for e in elements_raw.split(",") if e.strip()] if elements_raw else []
        element_energies_json_arg = (element_energies_json_arg or "").strip()
        preflight = (preflight_arg or "").strip() in ("1", "true", "True", "yes", "preflight")

        if repo_root_arg and os.path.isdir(repo_root_arg):
            sys.path.insert(0, repo_root_arg)

        from ase import Atoms

        from ip_orch.core.energy_correction import (
            wrap_linear_energy_correction,
            wrap_reference_energy_correction,
        )
        from ip_orch.core.model_factory import ModelFactory

        calc = ModelFactory.create(model_name_arg, models_path=models_path_arg)

        if (linear_a is None) ^ (linear_b is None):
            raise ValueError("Provide both a and b (or neither).")

        # Optional: compute element reference energies using the MLIP calculator itself.
        element_energies: Optional[Dict[str, float]] = None
        if element_energies_json_arg:
            try:
                element_energies = json.loads(element_energies_json_arg)
            except Exception as exc:
                raise ValueError(f"Failed to parse element energies JSON: {exc}")
        elif elements:
            element_energies = {}
            for sym in elements:
                # Single atom in a large non-periodic box.
                atom = Atoms(sym, positions=[(0.0, 0.0, 0.0)], cell=(20.0, 20.0, 20.0), pbc=False)
                atom.calc = calc
                element_energies[sym] = float(atom.get_potential_energy())

        if preflight:
            logger.info("IPORCH_ELEMENT_ENERGIES=%s", json.dumps(element_energies or {}))
            return

        calc = wrap_linear_energy_correction(calc, a=linear_a, b=linear_b, mode=linear_mode)
        calc = wrap_reference_energy_correction(calc, element_energies=element_energies)

        if not os.path.exists(user_script_path):
            logger.error("[Worker ERROR] User script not found: %s", user_script_path)
            sys.exit(1)

        spec = importlib.util.spec_from_file_location("user_logic", user_script_path)
        if spec is None or spec.loader is None:
            logger.error("[Worker ERROR] Could not load user script: %s", user_script_path)
            sys.exit(1)

        user_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_module)

        preferred = [
            "main",
            "mlip_entry",
            "your_function",
            "calculators_test",
            "run",
        ]
        logic_function = None
        for name in preferred:
            fn = getattr(user_module, name, None)
            if callable(fn):
                logic_function = fn
                break

        if logic_function is None:
            candidates = [
                (n, f)
                for n, f in inspect.getmembers(user_module, inspect.isfunction)
                if getattr(f, "__module__", None) == "user_logic"
            ]
            for _, fn in candidates:
                try:
                    if len(inspect.signature(fn).parameters) >= 2:
                        logic_function = fn
                        break
                except Exception:
                    continue

        if logic_function is None:
            names = ", ".join(n for n, _ in candidates) if "candidates" in locals() else "(none)"
            logger.error(
                "[Worker ERROR] Could not find a function to run. Define 'mlip_entry(calculator_name, calc)'. "
                "Found: %s",
                names,
            )
            sys.exit(1)

        logic_function(calculator_name_arg, calc)
    except Exception as e:
        calculator_name_arg = sys.argv[2] if len(sys.argv) > 2 else "unknown"
        logger.error("[Worker ERROR] Failure running %s: %s", calculator_name_arg, e)
        sys.exit(1)


if __name__ == "__main__":
    main()
