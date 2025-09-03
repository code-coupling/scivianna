from typing import IO, List, Tuple
import panel as pn

from scivianna.utils.polygonize_tools import PolygonElement


class Plotter2D:
    """Generic 2D geometry plotter interface"""

    def display_borders(self, display: bool):
        """Display or hides the figure borders and axis

        Parameters
        ----------
        display : bool
            Display if true, hides otherwise
        """
        raise NotImplementedError()

    def update_colorbar(self, display: bool, range: Tuple[float, float]):
        """Displays or hide the color bar, if display, updates its range

        Parameters
        ----------
        display : bool
            Display or hides the color bar
        range : Tuple[float, float]
            New colormap range
        """
        raise NotImplementedError()

    def set_color_map(self, color_map_name: str):
        """Sets the colorbar color map name

        Parameters
        ----------
        color_map_name : str
            Color map name
        """
        raise NotImplementedError()

    def plot_2d_frame(
        self,
        polygon_list: List[PolygonElement],
        compo_list: List[str],
        colors: List[Tuple[float, float, float]],
    ):
        """Adds a new plot to the figure from a set of polygons

        Parameters
        ----------
        polygon_list : List[PolygonElement]
            Polygons vertices vertical coordinates
        compo_names : Dict[Union[int, str], str]
            Composition associated to the polygons
        colors : List[Tuple[float, float, float]]
            Polygons colors
        """
        raise NotImplementedError()

    def update_2d_frame(
        self,
        polygon_list: List[PolygonElement],
        compo_list: List[str],
        colors: List[Tuple[float, float, float]],
    ):
        """Updates plot to the figure

        Parameters
        ----------
        polygon_list : List[PolygonElement]
            Polygons vertices vertical coordinates
        compo_list : List[str]
            Composition associated to the polygons
        colors : List[Tuple[float, float, float]]
            Polygons colors
        """
        raise NotImplementedError()

    def update_colors(self, compo_list: List[str], colors: List[Tuple[int, int, int]]):
        """Updates the colors of the displayed polygons

        Parameters
        ----------
        compo_list : List[str]
            Composition associated to the polygons
        colors : List[Tuple[int, int, int]]
            Polygons colors
        """
        raise NotImplementedError()

    def _set_callback_on_range_update(self, callback: IO):
        """Sets a callback to update the x and y ranges in the GUI.

        Parameters
        ----------
        callback : IO
            Function that takes x0, x1, y0, y1 as arguments
        """
        raise NotImplementedError()

    def make_panel(self) -> pn.viewable.Viewable:
        """Makes the Holoviz panel viewable displayed in the web app.

        Returns
        -------
        pn.viewable.Viewable
            Displayed viewable
        """
        raise NotImplementedError

    def _disable_interactions(
        self,
    ):
        """Disables de plot interactions for multi panel web-app resizing

        Parameters
        ----------
        disable : bool
            Disable if True, enable if False
        """
        raise NotImplementedError
