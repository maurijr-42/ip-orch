import os
from unittest.mock import patch

from ip_orch.core.model_factory import ModelFactory, _norm


def test_norm_function():
    assert _norm("MACE-MP-0") == "mace_mp_0"
    assert _norm("  ORB-V3  ") == "orb_v3"
    assert _norm("") == ""


@patch("ip_orch.core.model_factory.os.path.expanduser")
@patch.dict("sys.modules", {"deepmd.calculator": __import__("unittest.mock").mock.MagicMock()})
def test_create_dpa_models(mock_expanduser):
    mock_expanduser.side_effect = lambda x: x  # identity
    from deepmd.calculator import DP
        
    ModelFactory.create("dpa-3.1-3m-ft", models_path="/my/models/path")
    DP.assert_called_with(model=os.path.join("/my/models/path", "deepmd", "dpa3-openlam.pth"))
    
    ModelFactory.create("dpa-3.1-mptrj", models_path="/my/models/path")
    DP.assert_called_with(model=os.path.join("/my/models/path", "deepmd", "dpa3-mptrj.pth"))


@patch("ip_orch.core.model_factory.os.path.expanduser")
@patch.dict("sys.modules", {"nequip.ase": __import__("unittest.mock").mock.MagicMock()})
def test_create_nequip_models(mock_expanduser):
    mock_expanduser.side_effect = lambda x: x
    from nequip.ase import NequIPCalculator
    
    ModelFactory.create("nequip-oam-xl", models_path="/temp")
    NequIPCalculator.from_compiled_model.assert_called_with(
        compile_path=os.path.join("/temp", "nequip", "nequip-OAM-XL.nequip.pt2"), 
        device="cpu"
    )
