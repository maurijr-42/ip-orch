"""IP-Orch Python package interface.

The high-level orchestration API is imported lazily so target MLIP
environments can import ``ip_orch.core`` without also needing CLI dependencies.
"""

__all__ = [
    "IPOrch",
    "RunOptions",
    "orchestrate",
    "run",
    "run_with_options",
]


def __getattr__(name):
    if name in __all__:
        from .api import (
            IPOrch,
            RunOptions,
            orchestrate,
            run,
            run_with_options,
        )

        exports = {
            "IPOrch": IPOrch,
            "RunOptions": RunOptions,
            "orchestrate": orchestrate,
            "run": run,
            "run_with_options": run_with_options,
        }
        return exports[name]
    raise AttributeError(f"module 'ip_orch' has no attribute {name!r}")
