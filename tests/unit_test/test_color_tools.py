from typing import Any, Dict, List, Tuple, Union
import numpy as np
import multiprocessing as mp

from scivianna.data.data2d import Data2D
from scivianna.interface.generic_interface import Geometry2DPolygon
from scivianna.slave import OptionElement, set_colors_list
from scivianna.utils.polygonize_tools import PolygonCoords, PolygonElement
from scivianna.enums import VisualizationMode
from scivianna.constants import MESH

from scivianna.utils.color_tools import interpolate_cmap_at_values, get_edges_colors

class ColorTestInterface(Geometry2DPolygon):
    def __init__(self, ):
        """Interface built to test color tools."""
        pass

    def read_file(self, file_path: str, file_label: str):
        """Read a file and store its content in the interface

        Parameters
        ----------
        file_path : str
            File to read
        file_label : str
            Label to define the file type
        """
        pass

    def compute_2D_data(
        self,
        u: Tuple[float, float, float],
        v: Tuple[float, float, float],
        u_min: float,
        u_max: float,
        v_min: float,
        v_max: float,
        u_steps: int,
        v_steps: int,
        w_value: float,
        q_tasks: mp.Queue,
        options: Dict[str, Any],
    ) -> Tuple[Data2D, bool]:
        """Returns a list of polygons that defines the geometry in a given frame

        Parameters
        ----------
        u : Tuple[float, float, float]
            Horizontal coordinate director vector
        v : Tuple[float, float, float]
            Vertical coordinate director vector
        u_min : float
            Lower bound value along the u axis
        u_max : float
            Upper bound value along the u axis
        v_min : float
            Lower bound value along the v axis
        v_max : float
            Upper bound value along the v axis
        u_steps : int
            Number of points along the u axis
        v_steps : int
            Number of points along the v axis
        w_value : float
            Value along the u ^ v axis
        q_tasks : mp.Queue
            Queue from which get orders from the master.
        options : Dict[str, Any]
            Additional options for frame computation.

        Returns
        -------
        Data2D
            Geometry to display
        bool
            Were the polygons updated compared to the past call
        """
        return Data2D.from_polygon_list([
            PolygonElement(
                exterior_polygon=PolygonCoords(
                    x_coords = [],
                    y_coords = []
                ),
                holes = [],
                volume_id = i
            )
            for i in range(5)
        ]), True

    def get_labels(
        self,
    ) -> List[str]:
        """Returns a list of fields names displayable with this interface

        Returns
        -------
        List[str]
            List of fields names
        """
        return [MESH, "str", "float"]

    def get_value_dict(
        self, value_label: str, volumes: List[Union[int, str]], options: Dict[str, Any]
    ) -> Dict[Union[int, str], str]:
        """Returns a volume name - field value map for a given field name

        Parameters
        ----------
        value_label : str
            Field name to get values from
        volumes : List[Union[int,str]]
            List of volumes names
        options : Dict[str, Any]
            Additional options for frame computation.

        Returns
        -------
        Dict[Union[int,str], str]
            Field value for each requested volume names
        """
        if value_label == MESH:
            return {v: np.nan for v in volumes}
        elif value_label == "str":
            return {v: str(v) for v in volumes}
        elif value_label == "float":
            return {v: float(v) if v < 2 else np.nan for v in volumes}
        else:
            raise ValueError(f"Value label {value_label} not implemented. Keys available : MESH, str, and float.")


    def get_label_coloring_mode(self, label: str) -> VisualizationMode:
        """Returns wheter the given field is colored based on a string value or a float.

        Parameters
        ----------
        label : str
            Field to color name

        Returns
        -------
        VisualizationMode
            Coloring mode
        """
        if label == MESH:
            return VisualizationMode.NONE
        elif label == "str":
            return VisualizationMode.FROM_STRING
        elif label == "float":
            return VisualizationMode.FROM_VALUE
        else:
            raise ValueError(f"Label {label} not implemented. Keys available : MESH, str, and float.")


    def get_file_input_list(self) -> List[Tuple[str, str]]:
        """Returns a list of file label and its description for the GUI

        Returns
        -------
        List[Tuple[str, str]]
            List of (file label, description)
        """
        return []

    def get_options_list(self) -> List[OptionElement]:
        """Returns a list of options required by a code interface to add to the coordinate ribbon.

        Returns
        -------
        List[OptionElement]
            List of option objects.
        """
        return []
    

def test_interpolate_cmap_gray():
    colors = interpolate_cmap_at_values("gray", [0, 0.5, 1.])

    white = np.array((255, 255, 255, 255))
    black = np.array((0, 0, 0, 255))

    np.testing.assert_equal(colors, [black, (0.5*(black+white+np.array((1., 1., 1., 0.)))).astype(int), white])

def test_interpolate_cmap_blues():
    colors = interpolate_cmap_at_values("Blues", [0, 0.4, 1.])

    value_0 = np.array((247, 251, 255, 255))
    value_05 = np.array((147, 196, 222, 255))
    value_1 = np.array((8, 48, 107, 255))

    np.testing.assert_equal(colors, [value_0, value_05, value_1])

def test_color_list_none():
    interface = ColorTestInterface()
    data2D, _ = interface.compute_2D_data(None, None, 0, 1, 0, 1, 0, 0, 0, None, {})
    set_colors_list(data2D, interface, MESH, "gray", False, {})

    print(data2D.cell_colors)
    print(data2D.cell_edge_colors)
    raise ValueError()

def test_color_list_none():
    interface = ColorTestInterface()
    data2D, _ = interface.compute_2D_data(None, None, 0, 1, 0, 1, 0, 0, 0, None, {})
    set_colors_list(data2D, interface, MESH, "gray", False, {})

    np.testing.assert_equal(data2D.cell_colors, [(200, 200, 200, 0)]*5)
    np.testing.assert_equal(data2D.cell_edge_colors, [(180, 180, 180, 255)]*5)

def test_color_list_str():
    interface = ColorTestInterface()
    data2D, _ = interface.compute_2D_data(None, None, 0, 1, 0, 1, 0, 0, 0, None, {})
    set_colors_list(data2D, interface, "str", "gray", False, {})

    np.testing.assert_equal(data2D.cell_edge_colors, get_edges_colors(np.array(data2D.cell_colors)))

def test_color_list_float():
    interface = ColorTestInterface()
    data2D, _ = interface.compute_2D_data(None, None, 0, 1, 0, 1, 0, 0, 0, None, {})
    set_colors_list(data2D, interface, "float", "gray", False, {})

    white = np.array((255, 255, 255, 255))
    black = np.array((0, 0, 0, 255))
    transparent = np.array((200, 200, 200, 0))
    
    np.testing.assert_equal(data2D.cell_colors, [black, white, transparent, transparent, transparent])
    np.testing.assert_equal(data2D.cell_edge_colors, [
        (0, 0, 0, 255),
        (235, 235, 235, 255),
        [180, 180, 180, 255], 
        [180, 180, 180, 255], 
        [180, 180, 180, 255]
    ])
