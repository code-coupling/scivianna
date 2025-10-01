import matplotlib.pyplot as plt
import matplotlib.axes
from matplotlib.patches import Patch
from matplotlib.colors import to_rgb

from scivianna.slave import ComputeSlave

from typing import Dict, Tuple, Any

from scivianna.plotter_2d.polygon.matplotlib import Matplotlib2DPolygonPlotter
from scivianna.utils.color_tools import get_edges_colors
from scivianna.utils.polygon_sorter import PolygonSorter
from scivianna.enums import VisualizationMode

import numpy as np


def plot_frame_in_axes(
    slave: ComputeSlave,
    u: Tuple[float, float, float],
    v: Tuple[float, float, float],
    u_min: float,
    u_max: float,
    v_min: float,
    v_max: float,
    coloring_label: str,
    axes: matplotlib.axes.Axes,
    u_steps: int = 0,
    v_steps: int = 0,
    w_value: float = 0.0,
    color_map: str = "BuRd",
    display_colorbar: bool = False,
    options={},
    custom_colors: Dict[str, Dict[str, str]] = {},
    rename_values: Dict[str, Dict[str, str]] = {},
    legend_options: Dict[str, Any] = {},
):
    """Plots a geometry in a matplotlib axes object from an already initialized compute slave

    Parameters
    ----------
    slave : ComputeSlave
        Slave from which get the geometry polygons
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
    coloring_label : str
        Field to display in the plot
    axes : matplotlib.axes.Axes
        matplotlib axis object (obtainable from a plt.subplot call)
    u_steps : int
        Number of points along the u axis, by default "BuRd"
    v_steps : int
        Number of points along the v axis, by default "BuRd"
    w_value : float
        Value along the u ^ v axis, by default "BuRd"
    color_map : str, optional
        Colormap used to color the polygons, by default "BuRd"
    display_colorbar : bool, optional
        Display the polygons, by default False
    options : dict, optional
        Extra coloring options, by default {}
    custom_colors : Dict[str, Dict[str, str]], optional
        HTML color code per field value. Expects a dictionnary such as:
        {
            MATERIAL:{"iron" : #ffffff, "water" : #aa6868ff}
        }
        where MATERIAL is a displayed field name, and iron/water are its values. This parameter is only used for string based field.
    rename_values : Dict[str, Dict[str, str]], optional
        Renames the values present in the data for the legend. Expects a dictionnary such as:
        {
            MATERIAL:{"iron" : "Iron", "water" : "Water"}
        }
        where MATERIAL is a displayed field name, and iron/water are its values. This parameter is only used for string based field.
    legend_options : Dict[str, Any]
        Dictionnary of options provided when creating the legend
    """

    data, _ = slave.compute_2D_data(
        u=u,
        v=v,
        u_min=u_min,
        u_max=u_max,
        v_min=v_min,
        v_max=v_max,
        u_steps=u_steps,
        v_steps=v_steps,
        w_value=w_value,
        coloring_label=coloring_label,
        color_map=color_map,
        center_colormap_on_zero=False,
        options=options,
    )

    pw = PolygonSorter()
    pw.sort_from_value(
        data
    )

    plotter = Matplotlib2DPolygonPlotter()

    # Replacing provided colors
    if (
        slave.get_label_coloring_mode(coloring_label) == VisualizationMode.FROM_STRING
        and coloring_label in custom_colors
    ):
        compo_list = data.cell_values
        volume_color_list = data.cell_colors

        compos = np.unique(compo_list)

        for compo in compos:
            if compo in custom_colors[coloring_label]:
                color_array = np.array(
                    [
                        [
                            int(c * 255)
                            for c in to_rgb(custom_colors[coloring_label][compo])
                        ]
                        + [255]
                    ]
                    * len(compo_list)
                )
                compo_array = np.repeat(np.expand_dims(compo_list, axis=1), 4, axis=1)
                volume_color_list = np.where(
                    compo_array == compo, color_array, volume_color_list
                )

        data.cell_values = compo_list
        data.cell_colors = volume_color_list

    if display_colorbar:
        compo_list = data.cell_values
        volume_color_list = data.cell_colors
        if (
            slave.get_label_coloring_mode(coloring_label)
            == VisualizationMode.FROM_VALUE
        ):

            values = np.array(compo_list).astype(float)

            plotter.set_color_map(color_map)
            plotter.update_colorbar(True, (values.min(), values.max()))
        elif (
            slave.get_label_coloring_mode(coloring_label) == VisualizationMode.FROM_STRING
        ):
            compos = np.unique(compo_list)
            volume_color_list = np.array(volume_color_list).astype(float)

            edge_color_list = get_edges_colors(volume_color_list)

            colors = []
            edge_colors = []
            legend_compos = []

            volume_color_list /= 255.0
            edge_color_list /= 255.0

            for compo in compos:
                location = compo_list.index(compo)

                add_in_legend = True

                if coloring_label in rename_values:
                    if compo in rename_values[coloring_label]:
                        legend_compos.append(rename_values[coloring_label][compo])
                    else:
                        add_in_legend = False
                else:
                    legend_compos.append(compo)

                if add_in_legend:
                    colors.append(volume_color_list[location])
                    edge_colors.append(edge_color_list[location])
            
            legend_elements = [
                Patch(facecolor=c, edgecolor=ce, label=label)
                for c, ce, label in zip(colors, edge_colors, legend_compos)
            ]

            axes.legend(handles=legend_elements, **legend_options)
        else:
            raise ValueError(
                f"Can't display the colorbar of a field whose visualisation mode is not FROM_VALUE or FROM_STRING, found {slave.get_label_coloring_mode(coloring_label)}"
            )

    plotter.plot_2d_frame_in_axes(data, axes=axes)


def plot_frame(
    slave: ComputeSlave,
    u: Tuple[float, float, float],
    v: Tuple[float, float, float],
    u_min: float,
    u_max: float,
    v_min: float,
    v_max: float,
    coloring_label: str,
    u_steps: int = 0,
    v_steps: int = 0,
    w_value: float = 0.0,
    color_map: str = "BuRd",
    display_colorbar: bool = False,
    options={},
    custom_colors: Dict[str, Dict[str, str]] = {},
    rename_values: Dict[str, Dict[str, str]] = {},
    legend_options: Dict[str, Any] = {},
) -> Tuple[plt.Figure, matplotlib.axes.Axes]:
    """Creates a figure and plots a geometry in it from an already initialized compute slave

    Parameters
    ----------
    slave : ComputeSlave
        Slave from which get the geometry polygons
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
    coloring_label : str
        Field to display in the plot
    u_steps : int
        Number of points along the u axis, by default "BuRd"
    v_steps : int
        Number of points along the v axis, by default "BuRd"
    w_value : float
        Value along the u ^ v axis, by default "BuRd"
    color_map : str, optional
        Colormap used to color the polygons, by default "BuRd"
    display_colorbar : bool, optional
        Display the polygons, by default False
    options : dict, optional
        Extra coloring options, by default {}
    custom_colors : Dict[str, Dict[str, str]], optional
        HTML color code per field value. Expects a dictionnary such as:
        {
            MATERIAL:{"iron" : #ffffff, "water" : #aa6868ff}
        }
        where MATERIAL is a displayed field name, and iron/water are its values. This parameter is only used for string based field.
    rename_values : Dict[str, Dict[str, str]], optional
        Renames the values present in the data for the legend. Expects a dictionnary such as:
        {
            MATERIAL:{"iron" : "Iron", "water" : "Water"}
        }
        where MATERIAL is a displayed field name, and iron/water are its values. This parameter is only used for string based field.
    legend_options : Dict[str, Any]
        Dictionnary of options provided when creating the legend

    Returns
    ----------
        plt.Figure
            Figure containing the axes
        matplotlib.axes.Axes
            Axes in which the geometry was plotted
    """
    fig, axes = plt.subplots(1, 1)
    plot_frame_in_axes(
        slave=slave,
        u=u,
        v=v,
        u_min=u_min,
        u_max=u_max,
        v_min=v_min,
        v_max=v_max,
        coloring_label=coloring_label,
        axes=axes,
        u_steps=u_steps,
        v_steps=v_steps,
        w_value=w_value,
        color_map=color_map,
        display_colorbar=display_colorbar,
        options=options,
        custom_colors=custom_colors,
        rename_values=rename_values,
        legend_options=legend_options,
    )
    return fig, axes
