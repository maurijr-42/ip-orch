import logging

from ase.build import bulk

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main(calculator_name, ase_calculator):

    test_atoms = bulk("Cu", "fcc", a=3.6)

    if ase_calculator is None:
        logger.error("[error] calculator object is none")
        return
    else:
        test_atoms.calc = ase_calculator

    try:
        e = test_atoms.get_potential_energy()
        logger.info("[done] successfully evaluated energy: %s eV", e)
    except Exception:
        logger.error("[error] calculator imported, but failed to compute energy on H atom.")
        return
