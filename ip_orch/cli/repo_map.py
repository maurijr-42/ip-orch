MODEL_FAMILY_REPOS = {
    "chgnet": "https://github.com/CederGroupHub/chgnet",
    "deepmd": "https://github.com/deepmodeling/deepmd-kit",
    "eqnorm": "https://github.com/yzchen08/eqnorm",
    "grace": "https://github.com/ICAMS/grace-tensorpotential",
    "hienet": "https://github.com/divelab/AIRS/tree/main/OpenMat/HIENet",
    "m3gnet": "https://github.com/materialyzeai/m3gnet",
    "mace": "https://github.com/ACEsuit/mace",
    "matris": "https://github.com/HPC-AI-Team/MatRIS",
    "mattersim": "https://github.com/microsoft/mattersim",
    "nequip": "https://github.com/mir-group/nequip",
    "nequix": "https://github.com/atomicarchitects/nequix",
    "orb": "https://github.com/orbital-materials/orb-models",
    "sevenn": "https://github.com/MDIL-SNU/SevenNet",
    "tace": "https://github.com/xvzemin/tace",
    "upet": "https://github.com/lab-cosmo/upet",
}


def _matches_family(alias: str, family: str) -> bool:
    return alias == family or alias.startswith(f"{family}-") or alias.startswith(f"{family}_")


def repo_url_for_alias(alias: str) -> str:
    a = (alias or "").strip().lower()
    if _matches_family(a, "chgnet"):
        return MODEL_FAMILY_REPOS["chgnet"]
    if _matches_family(a, "dpa") or _matches_family(a, "deepmd"):
        return MODEL_FAMILY_REPOS["deepmd"]
    if _matches_family(a, "eqnorm"):
        return MODEL_FAMILY_REPOS["eqnorm"]
    if _matches_family(a, "grace"):
        return MODEL_FAMILY_REPOS["grace"]
    if _matches_family(a, "hienet"):
        return MODEL_FAMILY_REPOS["hienet"]
    if _matches_family(a, "m3gnet"):
        return MODEL_FAMILY_REPOS["m3gnet"]
    if _matches_family(a, "mace"):
        return MODEL_FAMILY_REPOS["mace"]
    if _matches_family(a, "matris"):
        return MODEL_FAMILY_REPOS["matris"]
    if _matches_family(a, "mattersim"):
        return MODEL_FAMILY_REPOS["mattersim"]
    if _matches_family(a, "nequip") or _matches_family(a, "allegro"):
        return MODEL_FAMILY_REPOS["nequip"]
    if _matches_family(a, "nequix"):
        return MODEL_FAMILY_REPOS["nequix"]
    if _matches_family(a, "orb"):
        return MODEL_FAMILY_REPOS["orb"]
    if _matches_family(a, "sevennet") or _matches_family(a, "sevenn"):
        return MODEL_FAMILY_REPOS["sevenn"]
    if _matches_family(a, "tace"):
        return MODEL_FAMILY_REPOS["tace"]
    if _matches_family(a, "upet") or _matches_family(a, "pet"):
        return MODEL_FAMILY_REPOS["upet"]
    return "-"
