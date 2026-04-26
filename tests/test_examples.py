import csv

import pytest


def test_graphene_bilayer_example_appends_one_csv_row(tmp_path, monkeypatch):
    """Run the graphene bilayer example and append one structured CSV result row."""

    pytest.importorskip("ase")
    from ase.calculators.calculator import Calculator, all_changes

    from examples import bilayer

    class ConstantEnergyCalculator(Calculator):
        implemented_properties = ["energy"]

        def calculate(self, atoms=None, properties=("energy",), system_changes=all_changes):
            super().calculate(atoms, properties, system_changes)
            self.results = {"energy": float(len(atoms))}

    csv_path = tmp_path / "bilayer-results.csv"
    monkeypatch.setenv("IPORCH_RESULTS_CSV", str(csv_path))

    bilayer.main("constant-model", ConstantEnergyCalculator())

    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    assert len(rows) == 1
    assert rows[0]["calculator_name"] == "constant-model"
    assert int(rows[0]["n_atoms"]) > 0


def test_isolated_atom_energies_script_appends_all_models_to_one_csv(tmp_path, monkeypatch):
    """Compute isolated atom energies and append all models to one CSV file."""

    pytest.importorskip("ase")
    from ase.calculators.calculator import Calculator, all_changes

    from ip_orch.scripts import isolated_atom_energies

    class AtomicNumberEnergyCalculator(Calculator):
        implemented_properties = ["energy"]

        def calculate(self, atoms=None, properties=("energy",), system_changes=all_changes):
            super().calculate(atoms, properties, system_changes)
            self.results = {"energy": float(atoms.numbers[0])}

    csv_path = tmp_path / "isolated_atom_energies.csv"
    monkeypatch.setenv("IPORCH_ATOM_RESULTS_CSV", str(csv_path))

    isolated_atom_energies.main("model-a", AtomicNumberEnergyCalculator())
    isolated_atom_energies.main("model-b", AtomicNumberEnergyCalculator())

    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))

    assert len(rows) == 236
    assert rows[0]["calculator_name"] == "model-a"
    assert rows[0]["symbol"] == "H"
    assert float(rows[0]["energy_ev"]) == 1.0
    assert rows[118]["calculator_name"] == "model-b"
    assert rows[118]["symbol"] == "H"
