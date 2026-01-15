from logging import warning
from typing import Callable, List, Tuple, Type
import numpy as np
import panel as pn
import param
import os

from scivianna.extension.extension import Extension
from scivianna.extension.field_selector import FieldSelector
from scivianna.extension.file_loader import FileLoader
from scivianna.panel.visualisation_panel import VisualizationPanel

try:
    from scivianna.extension.ai_assistant import AIAssistant
    has_agent = True

except ImportError as e:
    has_agent = False

    print(f"Warning : Agent not loaded, received error : {e}")

except ValueError as e:
    has_agent = False
    print(f"Warning : Agent not loaded, received error : {e}")


from scivianna.data.data3d import Data3D
from scivianna.interface.generic_interface import Geometry3D

from scivianna.enums import UpdateEvent, VisualizationMode
from scivianna.slave import ComputeSlave

from scivianna.plotter_3d.r3f_plotter import ReactThreeFiber3D
from scivianna.plotter_3d.generic_plotter import Plotter3D
from scivianna.constants import MESH

profile_time = bool(os.environ["VIZ_PROFILE"]) if "VIZ_PROFILE" in os.environ else 0
if profile_time:
    import time

pn.config.inline = True

default_extensions = [FileLoader, FieldSelector]
if has_agent:
    default_extensions.append(AIAssistant)


class Panel3D(VisualizationPanel):
    """2D Visualisation panel associated to a code."""

    plotter: Plotter3D
    """ 2D plotter displaying and updating the graph
    """
    current_data: Data3D
    """ Displayed data and their properties.
    """
    colormap = param.String()

    def __init__(
        self,
        slave: ComputeSlave,
        name="",
        extensions: List[Extension] = default_extensions
    ):
        """Visualization panel constructor

        Parameters
        ----------
        slave : ComputeSlave
            ComputeSlave object to which request the plots.
        name : str
            Name of the panel.
        display_polygons : bool
            Display as polygons or as a 2D grid.
        """
        code_interface: Type[Geometry3D] = slave.code_interface
        assert issubclass(
            code_interface, Geometry3D
        ), f"A VisualizationPanel can only be given a Geometry2D interface slave, received {code_interface}."

        #
        #   Initializing attributes
        #
        self.update_polygons = False
        """Need to update the data at the next async call"""

        self.field_change_callback: Callable = None
        """Function to call when the field is changed"""

        #
        #   Plotter creation
        #
        self.plotter = ReactThreeFiber3D()

        super().__init__(slave, name, extensions.copy())

        #
        #   First plot on XY basic range
        #
        self.displayed_field = MESH
        for extension in self.extensions:
            extension.on_field_change(MESH)

        self.colormap = "BuRd"

        self.x_range = (0., 1.)
        self.y_range = (0., 1.)
        self.z_range = (0., 1.)

        data_ = self.compute_fn(*self.x_range, *self.y_range, *self.z_range)

        self.plotter.plot_3d_frame(data_)

        self.current_data = data_

        if (
            slave.get_label_coloring_mode(self.displayed_field) == VisualizationMode.FROM_VALUE
        ):
            self.plotter.update_colorbar(
                True,
                (
                    min([float(e) for e in data_.cell_values]),
                    max([float(e) for e in data_.cell_values]),
                ),
            )
        else:
            self.plotter.update_colorbar(False, (None, None))

        self.__data_to_update: bool = False
        self.__new_data = {}

        try:
            pn.state.on_session_created(self.recompute)
        except Exception:
            pass

    @pn.io.hold()
    def async_update_data(
        self,
    ):
        """Update the figures and buttons based on what was added in self.__new_data. This function is called between two servers ticks to prevent multi-users collisions."""
        if self.__data_to_update:
            if profile_time:
                st = time.time()

            if "color_mapper" in self.__new_data:
                self.plotter.update_colorbar(
                    True,
                    (
                        self.__new_data["color_mapper"]["new_low"],
                        self.__new_data["color_mapper"]["new_high"],
                    ),
                )
                self.plotter.set_color_map(self.colormap)
            if "data" in self.__new_data:
                self.current_data: Data3D = self.__new_data["data"]

                if not self.update_polygons:
                    self.plotter.update_colors(self.current_data)
                else:
                    self.plotter.update_2d_frame(self.current_data)

            self.__data_to_update = False

            # this is necessary only in a notebook context where sometimes we have to force Panel/Bokeh to push an update to the browser
            pn.io.push_notebook(self.figure)

            if profile_time:
                print(f"Async function : {time.time() - st}")

        if "field_name" in self.__new_data:
            if self.marked_to_recompute:
                self.marked_to_recompute = False
                self.async_update_data()
        else:
            # If marked to recompute, a safe change was applied on a plot parameter, a recompute is requested async
            if self.marked_to_recompute:
                self.recompute()
                self.marked_to_recompute = False
                self.async_update_data()

        self.__new_data = {}

    def compute_fn(
        self,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        z_min: float,
        z_max: float,
    ) -> Data3D:
        """Request the slave to compute a new frame, and updates the data to display

        Parameters
        ----------
        x_min : float
            Lower bound value along the X axis
        x_max : float
            Upper bound value along the X axis
        y_min : float
            Lower bound value along the Y axis
        y_max : float
            Upper bound value along the Y axis
        z_min : float
            Lower bound value along the Z axis
        z_max : float
            Upper bound value along the Z axis

        Returns
        -------
        Data3D
            Geometry data.
        """
        options = {key: value for options in [
            e.provide_options() for e in self.extensions
        ] for key, value in options.items()}

        computed_data = self.slave.compute_3D_data(
            x_min,
            x_max,
            y_min,
            y_max,
            z_min,
            z_max,
            None,
            self.displayed_field,
            options,
        )

        if computed_data is None:
            print(
                f"\n\n Got None from computed data on {self.panel_name}, returning the past values.\n\n"
            )
            return None

        computed_data, polygons_updated = computed_data
        self.update_polygons = polygons_updated

        for extension in self.extensions:
            extension.on_updated_data(computed_data)

        return computed_data

    def ranges_callback(
        self,
        x0: float,
        x1: float,
        y0: float,
        y1: float,
        z0: float,
        z1: float,
    ):
        """Updates the bounds FloatInput based on the current frame zoom.

        Parameters
        ----------
        x0 : float
            X axis minimum value
        x1 : float
            X axis maximum value
        y0 : float
            Y axis minimum value
        y1 : float
            Y axis maximum value
        z0 : float
            Z axis minimum value
        z1 : float
            Z axis maximum value
        """
        to_update = {"x0": x0, "x1": x1, "y0": y0, "y1": y1, "z0": z0, "z1": z1}
        self.__new_data = {**self.__new_data, **to_update}
        pn.state.curdoc.add_next_tick_callback(self.async_update_data)

        self.x_range = (x0, x1)
        self.y_range = (y0, y1)
        self.z_range = (z0, z1)

        # for extension in self.extensions:
        #     extension.on_range_change((x0, x1), (y0, y1), self.w_value)

        if self.update_event == UpdateEvent.RANGE_CHANGE or (
            isinstance(self.update_event, list) and UpdateEvent.RANGE_CHANGE in self.update_event
        ):
            self.marked_to_recompute = True

    def recompute(
        self, *args, **kwargs
    ):
        """Recomputes the figure based on the new bounds and parameters.
        """
        if profile_time:
            st = time.time()

        print(
            f"{self.panel_name} - Recomputing for range {self.x_range},  {self.y_range},  {self.z_range}, with field {self.displayed_field}"
        )

        data = self.compute_fn(*self.x_range, *self.y_range, *self.z_range)

        if data is not None:
            if profile_time:
                print(f"Plot panel compute function : {time.time() - st}")
                st = time.time()

            self.__new_data = {
                "data": data,
            }

            if (
                self.slave.get_label_coloring_mode(
                    self.displayed_field
                ) == VisualizationMode.FROM_VALUE
            ):
                self.__new_data["color_mapper"] = {
                    "new_low": np.nanmin(np.array(data.cell_values).astype(float)),
                    "new_high": np.nanmax(np.array(data.cell_values).astype(float)),
                }
                self.__new_data["hide_colorbar"] = False
            else:
                self.__new_data["hide_colorbar"] = True

            self.__data_to_update = True

            if profile_time:
                print(f"Plot panel preparing data : {time.time() - st}")

            if pn.state.curdoc is not None:
                pn.state.curdoc.add_next_tick_callback(self.async_update_data)

    def duplicate(self, keep_name: bool = False) -> "VisualizationPanel":
        """Get a copy of the panel. A panel of the same type is generated, the current display too, but a new slave process is created.

        Parameters
        ----------
        keep_name : bool
            New panel name is the same as the current, if not, a number iterates at the end of the name

        Returns
        -------
        VisualizationPanel
            Copy of the visualisation panel
        """
        new_visualiser = Panel3D(
            slave=self.slave.duplicate(),
            name=self.panel_name,
            extensions=[e for e in self.extension_classes]
        )
        new_visualiser.copy_index = self.copy_index

        if isinstance(self.update_event, list):
            new_visualiser.update_event = self.update_event.copy()
        else:
            new_visualiser.update_event = self.update_event

        new_visualiser.set_field(self.displayed_field)
        new_visualiser.set_colormap(self.colormap)

        return new_visualiser

    def get_slave(
        self,
    ) -> ComputeSlave:
        """Returns the current panel code slave

        Returns
        -------
        ComputeSlave
            Panel slave
        """
        return self.slave

    def provide_on_mouse_move_callback(self, callback: Callable):
        """Stores a function to call everytime the user moves the mouse on the plot.
        Functions arguments are location, cell_id.

        Parameters
        ----------
        callback : Callable
            Function to call.
        """
        self.plotter.provide_on_mouse_move_callback(callback)

    def provide_on_clic_callback(self, callback: Callable):
        """Stores a function to call everytime the user clics on the plot.
        Functions arguments are location, cell_id.

        Parameters
        ----------
        callback : Callable
            Function to call.
        """
        self.plotter.provide_on_clic_callback(callback)

    def provide_field_change_callback(self, callback: Callable):
        """Stores a function to call everytime the displayed field is changed.
        the functions takes a string as argument.

        Parameters
        ----------
        callback : Callable
            Function to call.
        """
        self.field_change_callback = callback

    def recompute_at(self, position: Tuple[float, float, float], cell_id: str):
        """Triggers a panel recomputation at the provided location. Called by layout update event.

        Parameters
        ----------
        position : Tuple[float, float, float]
            Location to provide to the slave
        cell_id : str
            cell id to provide to the slave
        """
        x_span = self.x_range[1] - self.x_range[0]
        y_span = self.y_range[1] - self.y_range[0]
        z_span = self.z_range[1] - self.z_range[0]

        self.set_coordinates(
            position[0] - x_span / 2,
            position[0] + x_span / 2,
            position[1] - y_span / 2,
            position[1] + y_span / 2,
            position[2] - z_span / 2,
            position[2] + z_span / 2,
        )

    def set_coordinates(
        self,
        x_min: float = None,
        x_max: float = None,
        y_min: float = None,
        y_max: float = None,
        z_min: float = None,
        z_max: float = None,
    ):
        """Updates the plot coordinates

        Parameters
        ----------
        x_min : float
            Lower bound value along the X axis
        x_max : float
            Upper bound value along the X axis
        y_min : float
            Lower bound value along the Y axis
        y_max : float
            Upper bound value along the Y axis
        z_min : float
            Lower bound value along the Z axis
        z_max : float
            Upper bound value along the Z axis
        """
        self.__data_to_update = True

        update_range = False
        if x_min is not None:
            if not type(x_min) in [float, int]:
                raise TypeError(f"x_min must be a number, found type {type(x_min)}")
            if x_min != self.x_range[0]:
                update_range = True
        else:
            x_min = self.x_range[0]

        if y_min is not None:
            if not type(y_min) in [float, int]:
                raise TypeError(f"y_min must be a number, found type {type(y_min)}")
            if y_min != self.y_range[0]:
                update_range = True
        else:
            y_min = self.y_range[0]

        if z_min is not None:
            if not type(z_min) in [float, int]:
                raise TypeError(f"z_min must be a number, found type {type(z_min)}")
            if z_min != self.z_range[0]:
                update_range = True
        else:
            z_min = self.z_range[0]

        if x_max is not None:
            if not type(x_max) in [float, int]:
                raise TypeError(f"x_max must be a number, found type {type(x_max)}")
            if x_max != self.x_range[1]:
                update_range = True
        else:
            x_max = self.x_range[1]

        if y_max is not None:
            if not type(y_max) in [float, int]:
                raise TypeError(f"y_max must be a number, found type {type(y_max)}")
            if y_max != self.y_range[1]:
                update_range = True
        else:
            y_max = self.y_range[1]

        if z_max is not None:
            if not type(z_max) in [float, int]:
                raise TypeError(f"z_max must be a number, found type {type(z_max)}")
            if z_max != self.z_range[1]:
                update_range = True
        else:
            z_max = self.z_range[1]

        if update_range:
            self.x_range = (x_min, x_max)
            self.y_range = (y_min, y_max)
            self.z_range = (z_min, z_max)

            for extension in self.extensions:
                extension.on_range_change(self.x_range, self.y_range, self.z_range)

            self.plotter.set_axes(self.x_range, self.y_range, self.z_range)
            self.marked_to_recompute = True
            if pn.state.curdoc is not None:
                pn.state.curdoc.add_next_tick_callback(self.async_update_data)

    def set_field(self, field_name: str):
        """Updates the plotted field

        Parameters
        ----------
        field_name : str
            New field to display
        """
        if self.displayed_field != field_name:
            self.displayed_field = field_name

            if field_name not in self.slave.get_labels():
                warning(f"\n\nRequested field {field_name} : field unavailable, available values : {self.slave.get_labels()}.\n\n")

            else:
                for extension in self.extensions:
                    extension.on_field_change(field_name)

                if pn.state.curdoc is not None:
                    pn.state.curdoc.add_next_tick_callback(self.recompute)

                if self.field_change_callback is not None:
                    self.field_change_callback(field_name)

    def set_colormap(self, colormap: str):
        """Sets the current color map

        Parameters
        ----------
        colormap : str
            Color map name
        """
        if colormap != self.colormap:
            self.colormap = colormap
            self.__data_to_update = True

            if pn.state.curdoc is not None:
                pn.state.curdoc.add_next_tick_callback(self.recompute)
