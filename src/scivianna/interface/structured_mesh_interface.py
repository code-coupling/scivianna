
from typing import Any, Dict, List, Tuple, Union
import numpy as np
import multiprocessing as mp

from scivianna.data import Data2D
from scivianna.interface.generic_interface import Geometry2DPolygon
from scivianna.slave import OptionElement
from scivianna.utils.polygonize_tools import PolygonElement
from scivianna.enums import GeometryType, VisualizationMode
from scivianna.utils.structured_mesh import CarthesianStructuredMesh, StructuredMesh

from scivianna.constants import MESH


class StructuredMeshInterface(Geometry2DPolygon):
    """ StructuredMesh generic interface. This interface is not usable as such as it can't load a file. 
    To use it, the developper mush implement another interface inheriting from it implementing the read_file function.
    """

    polygons: List[PolygonElement]
    """Polygons computed at the previous iteration"""

    mesh: StructuredMesh
    """Mesh read from the .med file."""

    fields: Dict[str, np.ndarray]
    """Dictionnary containing the list of per cell value for each read field."""

    geometry_type=GeometryType._3D

    def __init__(self, ):
        """StructuredMesh interface constructor."""
        self.data: List[PolygonElement] = []
        self.last_computed_frame = []

    def read_file(self, file_path: str, file_label: str):
        """Read a file and store its content in the interface

        Parameters
        ----------
        file_path : str
            File to read
        file_label : str
            Label to define the file type
        """
        raise NotImplementedError()

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
        if (self.data is not None) and (
            self.last_computed_frame == [*u, *v, w_value]
        ):
            print("Skipping polygon computation.")
            return self.data, False

        self.last_computed_frame = [*u, *v, w_value]

        u = np.array(u)
        v = np.array(v)
        vec = np.cross(u, v)
        origin = u_min * u + v_min * v + w_value * vec

        self.data = Data2D.from_polygon_list(self.mesh.compute_2D_slice(origin, u, v))

        return self.data, True

    def get_labels(
        self,
    ) -> List[str]:
        """Returns a list of fields names displayable with this interface

        Returns
        -------
        List[str]
            List of fields names
        """
        labels = [MESH] + list(self.mesh.grids.keys())
        return labels

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
            return {v: np.NaN for v in volumes}

        return dict(zip(volumes, self.mesh.get_cells_values(value_label, volumes)))


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

        return VisualizationMode.FROM_VALUE

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

if __name__ == "__main__":
    from scivianna.slave import ComputeSlave
    from scivianna.panel.plot_panel import VisualizationPanel
    from scivianna.notebook_tools import _show_panel

    class MyMeshInterface(StructuredMeshInterface):
        def read_file(self, file_path: str, file_label: str):
            """Read a file and store its content in the interface

            Parameters
            ----------
            file_path : str
                File to read
            file_label : str
                Label to define the file type
            """
            size = 40
            self.mesh = CarthesianStructuredMesh(
                np.linspace(0, 4, size),
                np.linspace(0, 4, size),
                np.linspace(0, 4, size),
            )
            self.mesh.set_values("id", np.arange(size*size*size).reshape(size, size, size))
    
    slave = ComputeSlave(MyMeshInterface)
    slave.read_file(
        None,
        None,
    )

    _show_panel(VisualizationPanel(slave, name="StructuredMesh visualizer"))
