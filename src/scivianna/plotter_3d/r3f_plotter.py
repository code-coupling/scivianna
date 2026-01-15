from typing import IO, Callable, Tuple
import panel as pn

from scivianna.component.r3f_component.app import Data3DData, ReactThreeFiber
from scivianna.data.data3d import Data3D
from scivianna.utils.color_tools import color_maps


class ReactThreeFiber3D:
    """Generic 3D geometry plotter interface"""

    def __init__(self):
        self.rtf = ReactThreeFiber(
            sizing_mode="stretch_both",
            display_color_map=True,
            color_map_colors=color_maps["BuRd"],
            slice_tool_visible=True
        )

    def update_colorbar(self, display: bool, range: Tuple[float, float]):
        """Displays or hide the color bar, if display, updates its range

        Parameters
        ----------
        display : bool
            Display or hides the color bar
        range : Tuple[float, float]
            New colormap range
        """
        self.rtf.display_color_map = display
        self.rtf.color_bar_bounds = tuple(range)

    def set_color_map(self, color_map_name: str):
        """Sets the colorbar color map name

        Parameters
        ----------
        color_map_name : str
            Color map name
        """
        self.rtf.display_color_bar(
            color_maps[color_map_name],
            self.rtf.color_bar_bounds
        )

    def plot_3d_frame(
        self,
        data: Data3D,
    ):
        """Adds a new plot to the figure from a set of polygons

        Parameters
        ----------
        data : Data3D
            Data3D object containing the geometry to plot
        """
        self.rtf.plot_data3d(data)

    @pn.io.hold()
    def update_3d_frame(
        self,
        data: Data3D,
    ):
        """Updates plot to the figure

        Parameters
        ----------
        data : Data3D
            Data3D object containing the data to update
        """
        self.rtf.data_to_plot.clear()
        self.rtf.plot_data3d(data)

    def update_colors(self, data: Data3D,):
        """Updates the colors of the displayed polygons

        Parameters
        ----------
        data : Data3D
            Data3D object containing the data to update
        """
        current_data: Data3DData = self.rtf.data_to_plot[0]
        current_data.data.cell_colors = data.cell_colors
        current_data.data.cell_edge_colors = data.cell_edge_colors
        self.rtf.updata_data()

    def _set_callback_on_range_update(self, callback: IO):
        """Sets a callback to update the x and y ranges in the GUI.

        Parameters
        ----------
        callback : IO
            Function that takes x0, x1, y0, y1 as arguments
        """
        pass

    def make_panel(self) -> pn.viewable.Viewable:
        """Makes the Holoviz panel viewable displayed in the web app.

        Returns
        -------
        pn.viewable.Viewable
            Displayed viewable
        """
        return self.rtf

    def _disable_interactions(
        self,
    ):
        """Disables de plot interactions for multi panel web-app resizing

        Parameters
        ----------
        disable : bool
            Disable if True, enable if False
        """
        pass

    def provide_on_mouse_move_callback(self, callback: Callable):
        """Stores a function to call everytime the user moves the mouse on the plot.
        Functions arguments are location, cell_id.

        Parameters
        ----------
        callback : Callable
            Function to call.
        """
        self.on_mouse_move_callback = callback

    def provide_on_clic_callback(self, callback: Callable):
        """Stores a function to call everytime the user clics on the plot.
        Functions arguments are location, cell_id.

        Parameters
        ----------
        callback : Callable
            Function to call.
        """
        self.on_clic_callback = callback

    def set_axes(
        self,
        x_range: Tuple[float, float],
        y_range: Tuple[float, float],
        z_range: Tuple[float, float]
    ):
        """Stores the ranges axes of the current plot along X Y and Z axes

        Parameters
        ----------
        x_range : Tuple[float, float]
            Range along the X axis
        y_range : Tuple[float, float]
            Range along the Y axis
        z_range : Tuple[float, float]
            Range along the Z axis
        """
        pass
