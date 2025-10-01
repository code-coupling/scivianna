import numpy as np
import os
import multiprocessing as mp

import time
import pandas as pd
from typing import Any, List, Dict, Tuple, Type, Union

from scivianna.constants import OUTSIDE
from scivianna.data import Data2D
from scivianna.utils.color_tools import interpolate_cmap_at_values

from scivianna.interface.generic_interface import (
    GenericInterface,
    Geometry2D, 
    IcocoInterface, 
    ValueAtLocation, 
    Value1DAtLocation
)
from scivianna.interface.option_element import OptionElement
from scivianna.enums import VisualizationMode

from typing import TYPE_CHECKING

#   TYPE_CHECKING : Allows fake import of modules pylance work without importing them
if TYPE_CHECKING:
    import medcoupling

profile_time = bool(os.environ["VIZ_PROFILE"]) if "VIZ_PROFILE" in os.environ else 0
if profile_time:
    import time


class SlaveCommand:
    """Class defining the available commands that are forwarded to the compute slaves"""

    READ_FILE = "read_file"
    """Reads an input file"""
    GET_LABEL_LIST = "get_label_list"
    """Returns the list of displayable fields"""
    GET_FILE_INPUT_LIST = "get_file_input_list"
    """Returns the list of read input files"""
    GET_OPTIONS = "get_options"
    """Returns the list of options to display in the app"""
    COMPUTE_1D = "compute_1d"
    """Compute a 1D result"""
    COMPUTE_2D = "compute_2d"
    """Compute a 2D slice of the geometry"""
    GET_INPUT_MED_DOUBLEFIELD_TEMPLATE = "getInputMEDDoubleFieldTemplate"
    """Returns the med field template"""
    SET_INPUT_MED_DOUBLEFIELD = "setInputMEDDoubleField"
    """Sets an input field"""
    SET_INPUT_MED_DOUBLEFIELD = "setInputMEDDoubleField"
    """Sets an input field"""
    SET_INPUT_DOUBLE_VALUE = "setInputDoubleValue"
    """Sets a float"""
    SET_TIME = "setTime"
    """Sets the current time"""
    GET_COLORING_MODE = "get_label_coloring_mode"
    """Returns the coloring mode of a field"""
    GET_VALUE_DICT = "get_value_dict"
    """Returns the values of a field at cells"""


def set_colors_list(
    data: Data2D,
    code_interface: GenericInterface,
    coloring_label: str,
    color_map: str,
    center_colormap_on_zero: bool,
    options: Dict[str, Any],
):
    """Sets in a Data2D the list of colors for a field per polygon.

    Parameters
    ----------
    data : Data2D
        Geometry data
    code_interface : GenericInterface
        Code interface to request the field values
    coloring_label : str
        Field to color
    color_map : str
        Colormap in which select colors
    center_colormap_on_zero : bool
        Center the color map on zero
    options : Dict[str, Any]
        Plot extra options

    Raises
    ------
    NotImplementedError
        The field visualisation mode is not implemented.
    """
    if profile_time:
        start_time = time.time()

    if not isinstance(code_interface, Geometry2D):
        raise TypeError("get_color_list can only be called with a Geometry2D code interface.")
        
    coloring_mode = code_interface.get_label_coloring_mode(coloring_label)

    dict_value_per_volume = code_interface.get_value_dict(
        coloring_label, data.cell_ids, options
    )
    
    cell_values = [dict_value_per_volume[v] for v in data.cell_ids]
    
    if profile_time:
        print(f"get color list prepare time {time.time() - start_time}")
        start_time = time.time()

    if coloring_mode == VisualizationMode.FROM_STRING:
        """
        A random color is given for each string value.
        """
        sorted_values = np.sort(np.unique(list(dict_value_per_volume.values())))
        map_to = np.array([hash(c)%255 for c in sorted_values]) / 255

        value_list = np.array(cell_values)

        _, inv = np.unique(value_list, return_inverse=True)

        volume_colors = interpolate_cmap_at_values(
            color_map, map_to[inv].astype(float)
        )
        
        if OUTSIDE in data.cell_ids:
            for index_ in np.where(data.cell_ids == OUTSIDE):
                volume_colors[index_] = (255, 255, 255, 0)

    elif coloring_mode == VisualizationMode.FROM_VALUE:
        """
        The color is got from a color map set in the range (-max, max)
        """
        cell_values = np.array(cell_values).astype(float)
        no_nan_values = cell_values[~np.isnan(cell_values)]

        if profile_time:
            print(f"extracting no nan {time.time() - start_time}")
            start_time = time.time()

        if center_colormap_on_zero:
            if (
                len(no_nan_values) == 0 or max(abs(no_nan_values.min()), no_nan_values.max()) == 0.0
            ):
                minmax = 1.0
            else:
                minmax = max(abs(no_nan_values.min()), no_nan_values.max())

            cell_values = (cell_values + minmax) / (2 * minmax)
        else:
            if (
                len(no_nan_values) == 0 or max(abs(no_nan_values.min()), no_nan_values.max()) == 0.0
            ):
                minmax = 1.0
                min_val = 0.0
            elif no_nan_values.min() == no_nan_values.max():
                minmax = 1.0
                min_val = no_nan_values.min()
            else:
                minmax = no_nan_values.max() - no_nan_values.min()
                min_val = no_nan_values.min()

            cell_values = (cell_values - min_val) / minmax

        if profile_time:
            print(f"Rescaling data {time.time() - start_time}")
            start_time = time.time()

        volume_colors = interpolate_cmap_at_values(
            color_map, cell_values
        )

        if profile_time:
            print(f"Extracting colors {time.time() - start_time}")
            start_time = time.time()

        # Changing the main color from black to gray in case of Nan
        for c in range(len(volume_colors)):
            if volume_colors[c, 3] == 0.0:
                volume_colors[c] = (200, 200, 200, 0)

        if profile_time:
            print(f"Fixing nans {time.time() - start_time}")
            start_time = time.time()

    elif coloring_mode == VisualizationMode.NONE:
        """
        No color, mesh displayed only
        """
        volume_colors = np.array([(200, 200, 200, 0)] * (len(data.cell_ids)))
    else:
        raise NotImplementedError(
            f"Visualization mode {coloring_mode} not implemented."
        )
    
    data.cell_values = cell_values
    data.cell_colors = volume_colors.tolist()


def worker(
    q_tasks: mp.Queue,
    q_returns: mp.Queue,
    code_interface: Type[GenericInterface],
):
    """Creates a worker that will forward the panel requests to the GenericInterface on another process

    Parameters
    ----------
    q_tasks : mp.Queue
        Queue containing the tasks
    q_returns : mp.Queue
        Queue to return the results
    code_interface : Type[GenericInterface]
        GenericInterface to instanciate.
    """
    code_: GenericInterface = code_interface()

    while True:
        if not q_tasks.empty():
            task, data = q_tasks.get()

            if task == SlaveCommand.READ_FILE:
                code_.read_file(*data)
                q_returns.put("OK")

            elif task == SlaveCommand.GET_LABEL_LIST:
                labels = code_.get_labels()
                q_returns.put(labels)

            elif task == SlaveCommand.GET_FILE_INPUT_LIST:
                input_list = code_.get_file_input_list()
                q_returns.put(input_list)

            elif task == SlaveCommand.GET_OPTIONS:
                input_list = code_.get_options_list()
                q_returns.put(input_list)

            elif task == SlaveCommand.COMPUTE_1D:
                if not isinstance(code_, Value1DAtLocation):
                    raise TypeError(
                        f"The requested panel is not associated to an Value1DAtLocation, found class {type(code_)}."
                    )
                input_list = code_.get_1D_value(*data)
                q_returns.put(input_list)

            elif task == SlaveCommand.COMPUTE_2D:
                if profile_time:
                    st = time.time()
                (
                    u,
                    v,
                    u_min,
                    u_max,
                    v_min,
                    v_max,
                    u_steps,
                    v_steps,
                    w_value,
                    coloring_label,
                    color_map,
                    center_colormap_on_zero,
                    options,
                ) = data

                if not isinstance(code_, Geometry2D):
                    raise TypeError(
                        f"The requested panel is not associated to an Geometry2D, found class {type(code_)}."
                    )
                data, polygons_updated = code_.compute_2D_data(
                    u,
                    v,
                    u_min,
                    u_max,
                    v_min,
                    v_max,
                    u_steps,
                    v_steps,
                    w_value,
                    q_tasks,
                    options,
                )

                if profile_time:
                    print(f"Code compute 2D time : {time.time() - st}")
                    st = time.time()

                set_colors_list(
                    data,
                    code_,
                    coloring_label,
                    color_map,
                    center_colormap_on_zero,
                    options,
                )

                if profile_time:
                    print(f"Color list building time : {time.time() - st}")
                    st = time.time()

                q_returns.put(
                    [
                        data,
                        polygons_updated,
                    ]
                )

            elif task == SlaveCommand.GET_INPUT_MED_DOUBLEFIELD_TEMPLATE:
                if not isinstance(code_, IcocoInterface):
                    raise TypeError(
                        f"The requested panel is not associated to an IcocoInterface, found class {type(code_)}."
                    )
                field_name = data
                field_template: "medcoupling.MEDCouplingFieldDouble" = (
                    code_.getInputMEDDoubleFieldTemplate(field_name)
                )
                q_returns.put(field_template)

            elif task == SlaveCommand.SET_INPUT_MED_DOUBLEFIELD:
                if not isinstance(code_, IcocoInterface):
                    raise TypeError(
                        f"The requested panel is not associated to an IcocoInterface, found class {type(code_)}."
                    )
                field_name, field = data
                set_return = code_.setInputMEDDoubleField(field_name, field)
                q_returns.put(set_return)

            elif task == SlaveCommand.SET_TIME:
                time_ = data[0]
                if not isinstance(code_, IcocoInterface):
                    raise TypeError(
                        f"The requested panel is not associated to an IcocoInterface, found class {type(code_)}."
                    )
                set_return = code_.setTime(time_)
                q_returns.put(set_return)

            elif task == SlaveCommand.SET_INPUT_DOUBLE_VALUE:
                name, val = data
                if not isinstance(code_, IcocoInterface):
                    raise TypeError(
                        f"The requested panel is not associated to an IcocoInterface, found class {type(code_)}."
                    )
                set_return = code_.setInputDoubleValue(name, val)
                q_returns.put(set_return)

            elif task == SlaveCommand.GET_COLORING_MODE:
                field_name = data
                set_return = code_.get_label_coloring_mode(field_name)
                q_returns.put(set_return)

            elif task == SlaveCommand.GET_VALUE_DICT:
                if not isinstance(code_, Geometry2D):
                    raise TypeError(
                        f"The requested panel is not associated to an Geometry2D, found class {type(code_)}."
                    )
                set_return = code_.get_value_dict(*data)
                q_returns.put(set_return)


        else:
            time.sleep(0.1)


class ComputeSlave:
    """Class that creates a subprocess to interface with the code."""

    def __init__(self, code_interface: Type[GenericInterface]):
        """ComputeSlave constructor

        Parameters
        ----------
        code_interface : Type[GenericInterface]
            Class of the GenericInterface
        """
        self.p: mp.Process = None
        """ Subprocess hosting the worker
        """
        self.q_tasks: mp.Queue = None
        """ Queue in which the tasks are pushed
        """
        self.q_returns: mp.Queue = None
        """ Queue to get the results
        """
        self.code_interface: Type[GenericInterface] = code_interface
        """ Code interface class
        """
        self.file_read: List[Tuple[str, str]] = []
        """ List of file read and their associated key.
        """

        self.reset()

    def reset(
        self,
    ):
        """Kills the worker and create a new one."""
        print("RESETING SLAVE.")
        if self.p is not None:
            self.p.kill()

        self.q_tasks = mp.Queue()
        self.q_returns = mp.Queue()
        self.p = mp.Process(
            target=worker, args=(self.q_tasks, self.q_returns, self.code_interface)
        )
        self.p.start()

    def read_file(self, file_path: str, file_label: str):
        """Forwards to the worker a file path to read and its associated label

        Parameters
        ----------
        file_path : str
            File to read
        file_label : str
            File label
        """
        print("Reading file", file_path)
        self.q_tasks.put((SlaveCommand.READ_FILE, [str(file_path), file_label]))

        self.file_read.append((str(file_path), file_label))

        function_return = self.q_returns.get()
        assert function_return == "OK"

    def get_label_list(
        self,
    ) -> List[str]:
        """Get from the interface the list of displayable labels (fields list)

        Returns
        -------
        List[str]
            List of labels
        """
        self.q_tasks.put([SlaveCommand.GET_LABEL_LIST, None])

        return self.q_returns.get()

    def get_file_input_list(
        self,
    ) -> List[Tuple[str, str]]:
        """Get from the interface the list of files labels and their description

        Returns
        -------
        List[Tuple[str, str]]
            List of (file label, description)
        """
        self.q_tasks.put([SlaveCommand.GET_FILE_INPUT_LIST, None])

        return self.q_returns.get()

    def get_options(self) -> List[OptionElement]:
        """Get from the interface the list of options to add to the bounds ribbon.

        Returns
        -------
        List[OptionElement]
            List of options
        """
        self.q_tasks.put([SlaveCommand.GET_OPTIONS, None])

        return self.q_returns.get()

    def get_1D_value(
        self,
        position: Tuple[float, float, float],
        volume_index: str,
        material_name: str,
        field: str,
    ) -> Union[pd.Series, List[pd.Series]]:
        """Provides the 1D value of a field from either the (x, y, z) position, the volume index, or the material name.

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
        Union[pd.Series, List[pd.Series]]
            Field value
        """
        self.q_tasks.put(
            [
                SlaveCommand.COMPUTE_1D,
                [
                    position,
                    volume_index,
                    material_name,
                    field,
                ],
            ]
        )

        data = self.q_returns.get()
        return data
    
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
        coloring_label: str,
        color_map: str,
        center_colormap_on_zero: bool,
        options: Dict[str, Any],
    ) -> Tuple[
        Data2D, bool
    ]:
        """Get the geometry from the interface

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
        coloring_label : str
            Field label to display
        color_map : str
            Colormap in which select colors
        center_colormap_on_zero : bool
            Center the color map on zero
        options : Dict[str, Any]
            Additional options for frame computation.

        Returns
        -------
        Tuple[Data2D, bool]
            Data2D object containing the geometry, whether the polygons were updated
        """
        self.q_tasks.put(
            [
                SlaveCommand.COMPUTE_2D,
                [
                    u,
                    v,
                    u_min,
                    u_max,
                    v_min,
                    v_max,
                    u_steps,
                    v_steps,
                    w_value,
                    coloring_label,
                    color_map,
                    center_colormap_on_zero,
                    options,
                ],
            ]
        )

        data = self.q_returns.get()
        return data

    def duplicate(
        self,
    ) -> "ComputeSlave":
        """Returns a duplicate of the current ComputeSlave. The copy is reseted, and reads the file history.

        Returns
        -------
        ComputeSlave
            ComputeSlave copy.
        """
        duplicata = ComputeSlave(self.code_interface)

        duplicata.reset()

        for f in self.file_read:
            duplicata.read_file(f[0], f[1])

        return duplicata

    def getInputMEDDoubleFieldTemplate(
        self, fieldName: str
    ) -> "medcoupling.MEDCouplingFieldDouble":
        """Returns the med template in which cast the field set.

        Parameters
        ----------
        fieldName: str
            Field name
        """
        self.q_tasks.put([SlaveCommand.GET_INPUT_MED_DOUBLEFIELD_TEMPLATE, fieldName])

        return self.q_returns.get()

    def setInputMEDDoubleField(
        self, fieldName: str, aField: "medcoupling.MEDCouplingFieldDouble"
    ):
        """Updates a field in the interface.

        Parameters
        ----------
        fieldName: str
            Field name
        aField : medcoupling.MEDCouplingFieldDouble
            New field value
        """
        self.q_tasks.put([SlaveCommand.SET_INPUT_MED_DOUBLEFIELD, [fieldName, aField]])

        return self.q_returns.get()

    def setInputDoubleValue(self, name: str, val: float):
        """Set the current time in an interface to associate to the received value.

        Parameters
        ----------
        name : str
            Name associated to the set value
        time : float
            Current time
        """
        self.q_tasks.put([SlaveCommand.SET_INPUT_DOUBLE_VALUE, [name, val]])

        return self.q_returns.get()

    def setTime(self, time_:float):
        """Set the current time in an interface to associate to the received value.

        Parameters
        ----------
        time_ : float
            Current time
        """
        self.q_tasks.put([SlaveCommand.SET_TIME, [time_]])

        return self.q_returns.get()

    def get_value_dict(self, field_name: str) -> VisualizationMode:
        """Returns the coloring mode of the plot

        Parameters
        ----------
        field_name : str
            Name of the displayed field

        Returns
        -------
        VisualizationMode
            Coloring mode
        """
        self.q_tasks.put([SlaveCommand.GET_VALUE_DICT, field_name])

        return self.q_returns.get()

    def get_label_coloring_mode(self, field_name: str) -> VisualizationMode:
        """Returns the coloring mode of the plot

        Parameters
        ----------
        field_name : str
            Name of the displayed field

        Returns
        -------
        VisualizationMode
            Coloring mode
        """
        self.q_tasks.put([SlaveCommand.GET_COLORING_MODE, field_name])

        return self.q_returns.get()

    def terminate(
        self,
    ):
        """Terminates the subprocess"""
        self.p.terminate()


if __name__ == "__main__":
    pass
