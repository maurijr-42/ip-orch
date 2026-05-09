import os
import subprocess

from .helpers import DEFAULT_MODELS_BY_ENV


def _discover_conda_envs() -> set[str]:
    try:
        out = subprocess.check_output(["conda", "env", "list"], text=True)
        envs = []
        for line in out.splitlines():
            if line.strip().startswith("#"):
                continue
            parts = [p for p in line.split() if p]
            if parts:
                envs.append(parts[0])
        return set(e for e in envs if e and e != "#")
    except Exception:
        return set()


def _guess_envs_dir() -> str:
    candidates = [
        os.path.join(os.path.expanduser("~"), "miniconda3", "envs"),
        os.path.join(os.path.expanduser("~"), "anaconda3", "envs"),
        os.path.join(os.environ.get("CONDA_PREFIX", os.path.expanduser("~")), "envs"),
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    return candidates[0]


def _discover_envs_from_dir(base_dir: str) -> set:
    envs = set()
    if not base_dir:
        return envs
    path = os.path.expanduser(base_dir)
    if not os.path.isdir(path):
        return envs

    def has_python(d: str) -> bool:
        return os.path.isfile(os.path.join(d, "bin", "python")) or os.path.isfile(
            os.path.join(d, "Scripts", "python.exe")
        )

    try:
        for name in os.listdir(path):
            full = os.path.join(path, name)
            if os.path.isdir(full) and has_python(full):
                envs.add(name)
    except Exception:
        pass
    return envs


def _current_conda_env() -> str:
    return os.environ.get("CONDA_DEFAULT_ENV") or os.path.basename(os.environ.get("CONDA_PREFIX", ""))


def _normalize_token(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def _match_known_token(env_name: str) -> str:
    nenv = _normalize_token(env_name)
    for token in DEFAULT_MODELS_BY_ENV.keys():
        if _normalize_token(token) in nenv:
            return token
    return ""


def _python_for_env(env_name: str, base_dir: str) -> str:
    candidates = []
    if _is_path_like_env(env_name):
        for root in _path_like_roots(env_name):
            candidates.extend(_python_candidates(root))

    if not base_dir:
        return _first_executable(candidates)

    base = os.path.expanduser(base_dir)
    roots = [os.path.join(base, env_name), os.path.join(base, f".{env_name}")]
    if _is_path_like_env(env_name):
        roots.append(os.path.join(base, os.path.basename(os.path.normpath(env_name))))
        roots.append(os.path.join(base, f".{os.path.basename(os.path.normpath(env_name))}"))
    for root in roots:
        candidates.extend(_python_candidates(root))
    return _first_executable(candidates)


def _is_path_like_env(env_name: str) -> bool:
    env_name = env_name or ""
    return (
        env_name.startswith(("./", "../", "~/", "/"))
        or os.path.sep in env_name
        or bool(os.path.altsep and os.path.altsep in env_name)
    )


def _python_candidates(root: str) -> list[str]:
    return [
        os.path.join(root, "bin", "python"),
        os.path.join(root, "Scripts", "python.exe"),
    ]


def _path_like_roots(env_name: str) -> list[str]:
    root = os.path.expanduser(env_name)
    if not os.path.isabs(root):
        return [
            os.path.abspath(root),
            os.path.abspath(os.path.join(os.getcwd(), "..", root)),
            root,
        ]
    return [root]


def _first_executable(candidates: list[str]) -> str:
    for p in candidates:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return ""
