from typing import Any, Dict, List, Tuple, Union
import multiprocessing as mp
import numpy as np

from scivianna.interface.generic_interface import Geometry2DGrid
from scivianna.constants import MATERIAL, MESH
from scivianna.slave import ComputeSlave
from scivianna.panel.plot_panel import VisualizationPanel
from scivianna.utils.polygonize_tools import PolygonElement
from scivianna.enums import GeometryType, UpdateEvent, VisualizationMode
from scivianna.data import Data2D
from scivianna.interface.option_element import IntOption, OptionElement
from scivianna.layout.split import SplitDirection, SplitItem, SplitLayout


class MandelBrotInterface(Geometry2DGrid):
    geometry_type: GeometryType = GeometryType._2D

    def __init__(
        self,
    ):
        """Antares interface constructor."""
        self.data = None
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
    ) -> Tuple[List[PolygonElement], bool]:
        """Returns a list of data that defines the geometry in a given frame

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
        List[PolygonElement]
            List of data to display
        bool
            Were the data updated compared to the past call
        """
        if (
            self.data is not None
            and np.array_equal(np.array(u), np.array(self.last_computed_frame[0]))
            and np.array_equal(np.array(v), np.array(self.last_computed_frame[1]))
            and (u_min == self.last_computed_frame[2])
            and (u_max == self.last_computed_frame[3])
            and (v_min == self.last_computed_frame[4])
            and (v_max == self.last_computed_frame[5])
            and (u_steps == self.last_computed_frame[6])
            and (v_steps == self.last_computed_frame[7])
            and (w_value == self.last_computed_frame[8])
            and (options["Max iter"] == self.last_computed_frame[9]["Max iter"])
        ):
            print("Skipping polygon computation.")
            return self.data, False

        self.last_computed_frame = [
            u,
            v,
            u_min,
            u_max,
            v_min,
            v_max,
            u_steps,
            v_steps,
            w_value,
            options,
        ]

        # Script taken from:
        # https://gist.github.com/jfpuget/60e07a82dece69b011bb

        maxiter = options["Max iter"]

        def mandelbrot(z, maxiter):
            c = z
            for n in range(maxiter):
                if abs(z) > 2:
                    return n
                z = z * z + c
            return maxiter

        def mandelbrot_set(xmin, xmax, ymin, ymax, width, height, maxiter):
            r1 = np.linspace(xmin, xmax, width)
            r2 = np.linspace(ymin, ymax, height)
            return (
                r1,
                r2,
                [mandelbrot(complex(r, i), maxiter) for r in r1 for i in r2],
            )

        xvalues, yvalues, grid = mandelbrot_set(
            u_min, u_max, v_min, v_max, u_steps, v_steps, maxiter
        )

        self.data = Data2D.from_grid(
            np.array(grid).reshape((v_steps, u_steps), order="F"), xvalues, yvalues
        )

        return self.data, True

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
        if value_label == MATERIAL:
            dict_compo = {v: v for v in volumes}
            return dict_compo

        if value_label == MESH:
            dict_compo = {str(v): np.NaN for v in volumes}

            return dict_compo

        raise NotImplementedError(
            f"The field {value_label} is not implemented, fields available : {self.get_labels()}"
        )

    def get_labels(
        self,
    ) -> List[str]:
        """Returns a list of fields names displayable with this interface

        Returns
        -------
        List[str]
            List of fields names
        """
        labels = [MATERIAL, MESH]

        return labels

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
        if label in [MATERIAL]:
            return VisualizationMode.FROM_STRING

    def get_file_input_list(self) -> List[Tuple[str, str]]:
        """Returns a list of file label and its description for the GUI

        Returns
        -------
        List[Tuple[str, str]]
            List of (file label, description)
        """
        return []

    def get_options_list(self) -> List[OptionElement]:
        return [
            IntOption("Max iter", 30, "Maximum iteration in the mendebrot calculation")
        ]


def make_panel(_, return_slaves=False):
    slave = ComputeSlave(MandelBrotInterface)
    panel = VisualizationPanel(slave, name="Mandelbrot")
    panel.update_event = UpdateEvent.RANGE_CHANGE
    panel.step_inp.value = 2000

    slave_2 = ComputeSlave(MandelBrotInterface)
    panel_2 = VisualizationPanel(slave_2, name="Mandelbrot", display_polygons=False)
    panel_2.update_event = UpdateEvent.RANGE_CHANGE
    panel_2.step_inp.value = 2000

    layout = SplitLayout(
        SplitItem(panel, panel_2, SplitDirection.VERTICAL),
        additional_interfaces={"Mandelbrot": MandelBrotInterface},
    )

    if return_slaves:
        return layout, [slave, slave_2]
    else:
        return layout


if __name__ == "__main__":
    from scivianna.notebook_tools import _serve_panel

    _serve_panel(get_panel_function=make_panel, title="Mandelbrot set")
