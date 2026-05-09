from ip_orch.cli.helpers import _canonical_alias, _clean_env, _dedup_pairs, _group_pairs, _norm_token


def test_norm_token_keeps_only_alias_safe_characters():
    """Normalize free-form model names without losing dash/underscore aliases."""

    assert _norm_token(" MACE MP!! ") == "macemp"
    assert _norm_token("orb-v3_model") == "orb-v3_model"


def test_canonical_alias_maps_case_and_separator_variants_to_public_alias():
    """Resolve user-entered model names back to the public alias used in config."""

    assert _canonical_alias("MACE_MP_0") == "mace-mp-0"
    assert _canonical_alias("  ORB-v3  ") == "orb-v3"


def test_dedup_pairs_cleans_env_names_and_removes_duplicate_models():
    """Keep one canonical env/model pair after cleaning environment and alias spelling."""

    pairs = [
        [".mace", "MACE_MP_0"],
        ["mace", "mace-mp-0"],
        ["orb", "ORB_V3"],
    ]

    assert _dedup_pairs(pairs) == [["mace", "mace-mp-0"], ["orb", "orb-v3"]]


def test_group_pairs_canonicalizes_and_sorts_models_per_environment():
    """Group configured pairs into sorted model lists for display and summaries."""

    pairs = [["env", "ORB_V3"], ["env", "mace-mp"], ["other", "MACE_MP_0"]]

    assert _group_pairs(pairs) == {
        "env": ["mace-mp", "orb-v3"],
        "other": ["mace-mp-0"],
    }


def test_clean_env_strips_dot_prefix_used_by_hidden_conda_envs():
    """Normalize hidden conda env directory names before saving configuration."""

    assert _clean_env(" .orb ") == "orb"


def test_clean_env_preserves_relative_environment_paths():
    """Do not turn path-like virtualenv names such as ./mace into /mace."""

    assert _clean_env(" ./mace ") == "./mace"
    assert _clean_env("../mace") == "../mace"
