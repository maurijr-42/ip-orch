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
