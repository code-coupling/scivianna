from pathlib import Path

import pytest

import scivianna
from scivianna.constants import GEOMETRY, X, Y
from scivianna.interface.med_interface import MEDInterface
from scivianna.slave import ComputeSlave
from scivianna.utils.file_cleaner import mark_for_deletion


@pytest.mark.default
def test_save_load_med():
    """Simple test to make sure things happen before more tests are actually implemented
    """

    # Field example
    slave = ComputeSlave(MEDInterface)
    slave.read_file(
        Path(scivianna.__file__).parent / "input_file" / "power.med",
        GEOMETRY,
    )

    _, computed = slave.compute_2D_data(X, Y, 0., 1., 0., 1., 0., None, "INTEGRATED_POWER", {})
    assert computed, "First compute_2d_data should have been computed"
    slave.save("med_test.pkl")
    mark_for_deletion("med_test.pkl")

    slave2 = ComputeSlave(MEDInterface)
    slave2.load("med_test.pkl")

    _, computed = slave.compute_2D_data(X, Y, 0., 1., 0., 1., 0., None, "INTEGRATED_POWER", {})
    assert not computed, "Loaded compute_2d_data should have been skipped"

    slave.terminate()
