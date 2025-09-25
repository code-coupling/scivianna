from typing import IO, Any, Dict, List, Tuple, Union
from scivianna.utils.polygonize_tools import PolygonElement
from scivianna.plotter_2d.generic_plotter import Plotter2D

import matplotlib
import matplotlib.axes
import matplotlib.pyplot as plt
from matplotlib import cm, colormaps
from matplotlib import colors as plt_colors

from scivianna.constants import POLYGONS, VOLUME_NAMES, COMPO_NAMES, COLORS, EDGE_COLORS
from scivianna.utils.color_tools import get_edges_colors

from shapely import Polygon
import geopandas as gpd
import numpy as np

import panel as pn


class Matplotlib2DGridPlotter(Plotter2D):
    """2D geometry plotter based on the bokeh python module"""

    def __init__(
        self,
    ):
        """Creates the bokeh Figure and ColumnDataSources"""
        self.figure = plt.figure()
        self.ax = plt.axes()

        # self.colorbar = self.figure.colorbar(None)

        self.last_plot = {}
        plt.gca().set_aspect("equal")

        self.colormap_name = "BuRd"
        self.display_colorbar = False
        self.colorbar_range = (0.0, 1.0)

    def display_borders(self, display: bool):
        """Display or hides the figure borders and axis

        Parameters
        ----------
        display : bool
            Display if true, hides otherwise
        """
        if display:
            plt.axis("on")  # Hide the axis
        else:
            plt.axis("off")  # Hide the axis

    def update_colorbar(self, display: bool, range: Tuple[float, float]):
        """Displays or hide the color bar, if display, updates its range

        Parameters
        ----------
        display : bool
            Display or hides the color bar
        range : Tuple[float, float]
            New colormap range
        """
        self.display_colorbar = display
        self.colorbar_range = range

    def set_color_map(self, color_map_name: str):
        """Sets the colorbar color map name

        Parameters
        ----------
        color_map_name : str
            Color map name
        """
        self.colormap_name = color_map_name

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
        compo_list : List[str]
            Composition associated to the polygons
        colors : List[Tuple[float, float, float]]
            Polygons colors
        """
        self.plot_2d_frame_in_axes(polygon_list, compo_list, colors, self.ax, {})

    def plot_2d_frame_in_axes(
        self,
        polygon_list: List[PolygonElement],
        compo_list: List[str],
        colors: List[Tuple[float, float, float]],
        axes: matplotlib.axes.Axes,
        plot_options: Dict[str, Any] = {},
    ):
        """Adds a new plot to the figure from a set of polygons

        Parameters
        ----------
        polygon_list : List[PolygonElement]
            Polygons vertices vertical coordinates
        compo_list : List[str]
            Composition associated to the polygons
        colors : List[Tuple[float, float, float]]
            Polygons colors
        axes : matplotlib.axes.Axes
            Axes in which plot the figure
        plot_options : Dict[str, Any])
            Color options to be passed on to the actual plot function, such as edgecolor, facecolor, linewidth, markersize, alpha.
        """
        volume_list: List[Union[str, int]] = [p.volume_id for p in polygon_list]

        volume_colors: np.ndarray = np.array(colors).astype(float)
        volume_edge_colors: np.ndarray = get_edges_colors(volume_colors)

        polygons: List[Polygon] = [
            Polygon(
                shell=[
                    (p.exterior_polygon.x_coords[j], p.exterior_polygon.y_coords[j])
                    for j in range(len(p.exterior_polygon.x_coords))
                ],
                holes=[
                    [(h.x_coords[j], h.y_coords[j]) for j in range(len(h.x_coords))]
                    for h in p.holes
                ],
            )
            for p in polygon_list
        ]

        gdf = gpd.GeoDataFrame(geometry=polygons)

        volume_colors /= 255.0
        volume_edge_colors /= 255.0

        gdf.normalize().plot(
            facecolor=volume_colors.tolist(),
            edgecolor=volume_edge_colors.tolist(),
            ax=axes,
            **plot_options
        )

        if self.display_colorbar:
            plt.colorbar(
                cm.ScalarMappable(
                    norm=plt_colors.Normalize(
                        self.colorbar_range[0], self.colorbar_range[1]
                    ),
                    cmap=colormaps[self.colormap_name],
                ),
                ax=axes,
            )

        self.last_plot = {
            POLYGONS: polygons,
            VOLUME_NAMES: volume_list,
            COMPO_NAMES: compo_list,
            COLORS: volume_colors.tolist(),
            EDGE_COLORS: volume_edge_colors.tolist(),
        }

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
        self.plot_2d_frame(
            polygon_list,
            compo_list,
            colors,
        )

    def update_colors(self, compo_list: List[str], colors: List[Tuple[int, int, int]]):
        """Updates the colors of the displayed polygons

        Parameters
        ----------
        compo_list : List[str]
            Composition associated to the polygons
        colors : List[Tuple[int, int, int]]
            Polygons colors
        """
        self.plot_2d_frame(
            self.last_plot[POLYGONS],
            compo_list,
            colors,
        )

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
        raise NotImplementedError()

    def _disable_interactions(self, disable: bool):
        """Disables de plot interactions for multi panel web-app resizing

        Parameters
        ----------
        disable : bool
            Disable if True, enable if False
        """
        raise NotImplementedError()

    def get_resolution(self) -> Tuple[float, float]:
        """Returns the current plot resolution to display. For resolution based codes, it will be replaced by the value present in the gui

        Returns
        -------
        Tuple[float, float]
            Resolution if possible, else (None, None)
        """
        return None, None

    def export(self, file_name: str, title="Bokeh 2D plot"):
        """Exports the plot in a file

        Parameters
        ----------
        file_name : str
            Export file path
        """
        self.figure.suptitle(title)
        self.figure.tight_layout()
        self.figure.savefig(file_name, dpi=1500)

    def set_axes(self, u:Tuple[float, float, float], v:Tuple[float, float, float], w:float):
        """Stores the u v axes of the current plot

        Parameters
        ----------
        u : Tuple[float, float, float]
            Horizontal axis direction vector
        v : Tuple[float, float, float]
            Vertical axis direction vector
        w : float
            Normal vector coordinate
        """
        pass