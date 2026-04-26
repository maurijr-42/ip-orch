from ip_orch.cli.repo_map import MODEL_FAMILY_REPOS, repo_url_for_alias


def test_repo_url_for_alias_uses_exact_or_prefix_matching():
    """Avoid fragile substring matching between similarly named model families."""

    assert repo_url_for_alias("nequix-mp") == MODEL_FAMILY_REPOS["nequix"]
    assert repo_url_for_alias("nequip-oam-l") == MODEL_FAMILY_REPOS["nequip"]
    assert repo_url_for_alias("my-nequip-wrapper") == "-"


def test_repo_url_for_alias_maps_known_prefixes():
    """Map supported aliases to their upstream family repositories."""

    assert repo_url_for_alias("dpa-3.1-mptrj") == MODEL_FAMILY_REPOS["deepmd"]
    assert repo_url_for_alias("pet-oam-xl") == MODEL_FAMILY_REPOS["upet"]
