
from typing import List, Tuple, Union

import pytest
from scivianna.interface.generic_interface import ValueAtLocation
from scivianna.slave import ComputeSlave


class ThrowingErrorInterface(ValueAtLocation):
    def __init__(self, ):
        """Interface built to test error catching.
        """
        pass

    def get_value(
        self,
        position: Tuple[float, float, float],
        volume_index: str,
        material_name: str,
        field: str,
    ):
        """Provides the result value of a field from either the (x, y, z) position, the volume index, or the material name.

        Parameters
        ----------
        position : Tuple[float, float, float]
            Position at which the value is requested
        volume_index : str
            Index of the requested volume
        material_name : str
            Name of the requested material
        field : str
            Requested field name

        Returns
        -------
        List[Union[str, float]]
            Field value
        """
        raise ValueError("Testing valueError")

    def get_values(
        self,
        positions: List[Tuple[float, float, float]],
        volume_indexes: List[str],
        material_names: List[str],
        field: str,
    ) -> List[Union[str, float]]:
        """Provides the result values at different positions from either the (x, y, z) positions, the volume indexes, or the material names.

        Parameters
        ----------
        positions : List[Tuple[float, float, float]]
            List of position at which the value is requested
        volume_indexes : List[str]
            Indexes of the requested volumes
        material_names : List[str]
            Names of the requested materials
        field : str
            Requested field name

        Returns
        -------
        List[Union[str, float]]
            Field values
        """
        raise NotImplementedError("Testing NotImplementedError")

    def get_labels(self) -> List[str]:
        """Returns the fields names providable.

        Returns
        -------
        List[str]
            Fields names
        """
        raise RuntimeError("Testing RuntimeError")


@pytest.mark.default
def test_runtime_error():
    slave = ComputeSlave(ThrowingErrorInterface)
    try:
        slave.get_labels()
    except RuntimeError as e:
        assert True
        return
    else:
        assert False, "RuntimeError not caught"

@pytest.mark.default
def test_value_error():
    slave = ComputeSlave(ThrowingErrorInterface)
    try:
        slave.get_value(None, None, None, None)
    except ValueError as e:
        assert True
        return
    else:
        assert False, "ValueError not caught"

@pytest.mark.default
def test_notimplemented_error():
    slave = ComputeSlave(ThrowingErrorInterface)
    try:
        slave.get_values(None, None, None, None)
    except NotImplementedError as e:
        assert True
        return
    else:
        assert False, "NotImplementedError not caught"