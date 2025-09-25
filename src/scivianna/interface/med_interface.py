import os
from typing import Any, Dict, List, Tuple, Union
import numpy as np
import multiprocessing as mp

from scivianna.data import Data2D
from scivianna.interface.generic_interface import Geometry2DPolygon, IcocoInterface
from scivianna.interface.option_element import IntOption
from scivianna.slave import OptionElement
from scivianna.utils.polygonize_tools import PolygonElement, PolygonCoords
from scivianna.enums import GeometryType, VisualizationMode

import medcoupling

from scivianna.constants import MESH, GEOMETRY, CSV

profile_time = bool(os.environ["VIZ_PROFILE"]) if "VIZ_PROFILE" in os.environ else 0
if profile_time:
    import time


class MEDInterface(Geometry2DPolygon, IcocoInterface):

    polygons: List[PolygonElement]
    """Polygons computed at the previous iteration"""

    file_path: str
    """MEDCoupling .med file path saved to read MedCouplingFields later."""

    meshnames: List[str]
    """Names of the meshes stored in the .med file."""

    mesh: medcoupling.MEDCouplingUMesh
    """Mesh read from the .med file."""

    fieldnames: List[str]
    """Names of the fields stored in the .med file at the selected mesh name."""

    fields_iterations: Dict[str, List[Tuple[int, int]]]
    """List containing for tuples storing the field name, and the associated iteration."""

    fields: Dict[str, List[float]]
    """Dictionnary containing the list of per cell value for each read field."""

    cell_dict: Dict[int, int]
    """Dictionnary associating the 2D mesh cells to the 3D mesh cells"""

    """ Support mesh
    """
    
    geometry_type=GeometryType._3D

    def __init__(self):
        """MEDCoupling interface constructor."""
        self.data: List[PolygonElement] = None
        self.file_path = None
        self.meshnames = []
        self.mesh = None
        self.fieldnames = []
        self.last_computed_frame = []
        self.fields = {}
        self.fields_iterations = {}
        self.cell_dict = {}

    def read_file(self, file_path: str, file_label: str):
        """Read a file and store its content in the interface

        Parameters
        ----------
        file_path : str
            File to read
        file_label : str
            Label to define the file type
        """
        if file_label == GEOMETRY:
            if profile_time:
                start_time = time.time()
            print("File to read", file_path)
            self.file_path = file_path

            if not os.path.isfile(file_path):
                raise ValueError(f"Provided file name does not exist {file_path}")

            self.meshnames = medcoupling.GetMeshNames(file_path)
            self.fieldnames = medcoupling.GetAllFieldNamesOnMesh(
                file_path, self.meshnames[0]
            )

            self.fields_iterations = {}

            for field in self.fieldnames:
                components = medcoupling.GetComponentsNamesOfField(file_path, field)

                iterations = medcoupling.GetFieldIterations(
                    medcoupling.ON_CELLS, file_path, self.meshnames[0], field
                )

                for component in components:
                    for iteration in iterations:
                        self.fields_iterations[
                            (
                                "@".join([field, component[0]])
                                if component[0] != ""
                                else field
                            )
                        ] = [tuple(iteration)]

            self.mesh = medcoupling.ReadMeshFromFile(file_path, 0)

            if profile_time:
                print(f"File reading time {time.time() - start_time}")
        else:
            raise ValueError(f"File label '{file_label}' not implemented")

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

        if profile_time:
            start_time = time.time()

        self.last_computed_frame = [*u, *v, w_value]
        mesh_dimension = self.mesh.getMeshDimension()

        use_cell_id = True

        if mesh_dimension == 2:
            mesh: medcoupling.MEDCouplingUMesh = self.mesh
            cell_ids = list(range(mesh.getNumberOfCells()))
        elif mesh_dimension == 3:
            vec = [float(e) for e in np.cross(u, v)]
            origin = [u_min * u[i] + v_min * v[i] + w_value * vec[i] for i in range(3)]

            try:
                eps = 0.0
                mesh: medcoupling.MEDCouplingUMesh = self.mesh.buildSlice3D(
                    origin, vec, eps
                )[0]

                cells_ids = self.mesh.getCellIdsCrossingPlane(origin, vec, eps)

                cell_ids = [int(c) for c in cells_ids]
            except:
                eps = 1e-7
                mesh: medcoupling.MEDCouplingUMesh = self.mesh.buildSlice3D(
                    origin, vec, eps
                )[0]
                cell_ids = [
                    int(c) for c in self.mesh.getCellIdsCrossingPlane(origin, vec, eps)
                ]

            if len(cell_ids) != mesh.getNumberOfCells():
                use_cell_id = False
        else:
            raise ValueError(
                f"Mesh dimension is {mesh_dimension}, should be either 2 or 3 to be displayed."
            )

        if profile_time:
            print(f"Compute mesh time {time.time() - start_time}")
            start_time = time.time()

        cells_count = mesh.getNumberOfCells()

        self.data = []

        vertices_coords = [list(c) for c in mesh.getCoords()]
        self.cell_dict.clear()

        for cell in range(cells_count):
            x_vals = [
                vertices_coords[cell_id][0] for cell_id in mesh.getNodeIdsOfCell(cell)
            ]
            y_vals = [
                vertices_coords[cell_id][1] for cell_id in mesh.getNodeIdsOfCell(cell)
            ]
            z_vals = [
                vertices_coords[cell_id][2] if mesh_dimension == 3 else 0.0
                for cell_id in mesh.getNodeIdsOfCell(cell)
            ]

            coords = np.array([x_vals, y_vals, z_vals])

            u_vals = np.matmul(coords.T, u)
            v_vals = np.matmul(coords.T, v)

            self.data.append(
                PolygonElement(
                    exterior_polygon=PolygonCoords(x_coords=u_vals, y_coords=v_vals),
                    holes=[],
                    volume_id=str(cell),
                )
            )

            if not use_cell_id:
                self.cell_dict[cell] = self.mesh.getCellContainingPoint(
                    [np.mean(x_vals), np.mean(y_vals), np.mean(z_vals)], eps=0.0
                )

        if use_cell_id:
            self.cell_dict = dict(zip(list(range(cells_count)), cell_ids))

        if profile_time:
            print(
                f"Gathering cells id time: {time.time() - start_time} using cell id {use_cell_id}"
            )

        self.data = Data2D.from_polygon_list(self.data)
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
        labels = [MESH] + list(self.fields_iterations.keys())
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
        if profile_time:
            start_time = time.time()
        if value_label == MESH:
            return {str(v): np.NaN for v in volumes}

        field_np_array = None

        if value_label in self.fields:
            field_np_array = self.fields[value_label]
        else:
            print(f"Reading MEDCouplingFieldDouble in {self.file_path}")
            # print("Checking", value_label, "in", self.fields_iterations, field in self.fields_iterations.keys())

            if value_label in self.fields_iterations:
                # print("Checking ", (options["Iteration"], options["Order"]), (options["Iteration"], options["Order"]) in self.fields_iterations[value_label])
                options = {
                    "Iteration": self.fields_iterations[value_label][0][0],
                    "Order": self.fields_iterations[value_label][0][1],
                }
                # if "Iteration" in options and "Order" in options and (options["Iteration"], options["Order"]) in self.fields_iterations[value_label]:
                if True:
                    field_name = value_label.split("@")[0]
                    field: medcoupling.MEDCouplingFieldDouble = medcoupling.ReadField(
                        medcoupling.ON_CELLS,
                        self.file_path,
                        self.meshnames[0],
                        0,
                        field_name,
                        options["Iteration"],
                        options["Order"],
                    )
                    field_array: medcoupling.DataArrayDouble = field.getArray()
                    field_np_array: np.ndarray = field_array.toNumPyArray()

                    if "@" in value_label:
                        components: List[str] = field_array.getInfoOnComponents()
                        field_np_array = field_np_array[
                            :, components.index(value_label.split("@")[1])
                        ]
                    else:
                        field_np_array = field_np_array

            if field_np_array is not None:
                self.fields[value_label] = field_np_array

        if field_np_array is not None:
            indexes = np.array(list(self.cell_dict.values())).astype(int)
            values = field_np_array[indexes[np.array(volumes).astype(int)]]

            value_dict = dict(zip(np.array(volumes).astype(str), values))

            if profile_time:
                print(f"Get value dict time: {time.time() - start_time}")
            return value_dict

        raise NotImplementedError(
            f"The field {value_label} is not implemented, fields available : {self.get_labels()}"
        )

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
        return [(GEOMETRY, "MED file."), (CSV, "CSV result file.")]

    def getInputMEDDoubleFieldTemplate(self, field_name: str):
        mcfield = medcoupling.MEDCouplingFieldDouble(
            medcoupling.ON_CELLS, medcoupling.ONE_TIME
        )
        mcfield.setName(field_name)
        mcfield.setTime(0.0, 0, 0)
        mcfield.setMesh(self.mesh)
        array = medcoupling.DataArrayDouble([0.0] * self.mesh.getNumberOfCells())
        mcfield.setArray(array)
        if field_name in self.fields:
            mcfield.setNature(self.fields[field_name].getNature())
        else:
            print(
                field_name,
                f"not found in self.fields, available keys: {list(self.fields.keys())}.",
            )
        return mcfield

    def setInputMEDDoubleField(
        self, field_name: str, field: medcoupling.MEDCouplingFieldDouble
    ):
        self.fields[field_name] = field

    def setTime(self, time_:float):
        pass
    
    def get_options_list(self) -> List[OptionElement]:
        """Returns a list of options required by a code interface to add to the coordinate ribbon.

        Returns
        -------
        List[OptionElement]
            List of option objects.
        """
        return [
            IntOption("Iteration", -1, "Med field iteration."),
            IntOption("Order", -1, "MED field order."),
        ]


if __name__ == "__main__":
    from scivianna.slave import ComputeSlave
    from scivianna.panel.plot_panel import VisualizationPanel
    from scivianna.notebook_tools import _show_panel

    slave = ComputeSlave(MEDInterface)
    # slave.read_file("/volatile/catA/tmoulignier/Workspace/some_holoviz/jdd/mesh_hexa_3d.med", GEOMETRY)
    slave.read_file(
        "/volatile/catA/tmoulignier/Workspace/some_holoviz/src/scivianna/default_jdd/INTEGRATED_POWER.med",
        GEOMETRY,
    )

    _show_panel(VisualizationPanel(slave, name="MED visualizer"))
