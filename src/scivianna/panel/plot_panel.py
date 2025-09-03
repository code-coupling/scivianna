from typing import Dict, List, Any, Tuple, Union
import numpy as np
import panel as pn
import os
import functools

from scivianna.interface.generic_interface import Geometry2D
from scivianna.interface.option_element import OptionElement
from scivianna.components.overlay_component import Overlay
from scivianna.components.server_file_browser import ServerFileBrowser
from scivianna.enums import GeometryType, VisualizationMode
from scivianna.slave import ComputeSlave

from scivianna.utils.polygonize_tools import PolygonElement, PolygonSorter
from scivianna.plotter_2d.bokeh import Bokeh2DPlotter
from scivianna.plotter_2d.generic_plotter import Plotter2D
from scivianna.constants import GEOMETRY, COLORS, COMPO_NAMES, VOLUME_NAMES, POLYGONS
from scivianna.utils.color_tools import beautiful_color_maps

profile_time = bool(os.environ["VIZ_PROFILE"]) if "VIZ_PROFILE" in os.environ else 0
if profile_time:
    import time

pn.config.inline = True  # necessary if your system does not have internet access due to CEA liste blanche
pn.extension(
    "tabulator", design="material", template="material", loading_indicator=True
)  # necessary to have Panel/Bokeh in a Notebook

class VisualizationPanel:
    """Visualisation panel associated to a code."""

    main_frame: Overlay
    """ Main frame displaying the geometry.
    """
    side_bar: pn.Column
    """ Side bar where select files to import, and the plot axes
    """

    bounds_row: pn.Row
    """ Row with widgets to define the bounds of the plot and additional options
    """

    slave: ComputeSlave
    """ Slave to which request the plots
    """

    plotter: Plotter2D
    """ 2D plotter displaying and updating the graph
    """
    name: str
    """ Panel name
    """

    current_polygons: Dict[str, Any]
    """ Displayed polygons and their properties.
    """
    # source_coordinates:ColumnDataSource
    # """ ColumnDataSource object that stores the figure coordinates.
    # """

    def __init__(self, slave: ComputeSlave, name=""):
        """Visualization panel constructor

        Parameters
        ----------
        slave : ComputeSlave
            ComputeSlave object to which request the plots.
        name : str
            Name of the panel.
        """
        self.name = name
        self.copy_index = 0
        self.slave = slave
        self.bounds_row = None
        self.update_polygons = False
        """Need to update the polygons at the next async call"""

        code_interface:Geometry2D = self.slave.code_interface
        self.geometry_type:GeometryType = code_interface.geometry_type
        self.rasterized:bool = code_interface.rasterized

        self.polygon_worker = PolygonSorter()

        self.__data_to_update: bool = False
        self.__range_to_update: bool = False
        """Is it required to update the data, can be set on periodic event or on clic"""
        self.__new_data = {}
        """New data to set in the colorbar and in the columndatasources"""
        """
            Widget To send the input file
        """

        if not os.path.isdir("jdd"):
            os.makedirs("jdd")

        self.file_browsers: Dict[str, ServerFileBrowser] = {}
        load_files_label = """
            Load input files
        """

        def load_file(event, browser_name:str):
            """Request the slave to load an input file. If the file is a geometry file, the slave is reseted

            Parameters
            ----------
            data : Any
                File input data property.
            """
            file_path = self.file_browsers[browser_name].selected_file

            if file_path is not None:
                if browser_name == GEOMETRY:
                    self.slave.reset()

                self.slave.read_file(
                    file_path, browser_name
                )

                self.field_color_selector.options = list(
                    set(
                        self.field_color_selector.options + self.slave.get_label_list()
                    )
                )

                recompute_cb(None)

        file_input_list = self.slave.get_file_input_list()

        for name, description in file_input_list:
            self.file_browsers[name] = ServerFileBrowser(
                name=name
                # , sizing_mode="stretch_width"
                #, description=description
            )
            self.file_browsers[name].param.watch(functools.partial(load_file, browser_name=name), "selected_file")

        select_coloring_label = """
            Color field
        """
        fields_list = self.slave.get_label_list()
        self.field_color_selector = pn.widgets.MultiChoice(
            name="Color field",
            options=fields_list,
            value=[fields_list[0]],
            max_items=1,
            #   option_limit =1,
            #   placeholder="Select the field to display."
        )

        u_min = 0.0
        u_max = 2.0
        v_min = 0.0
        v_max = 2.0
        z = 0.5

        self.color_map_selector = pn.widgets.ColorMap(
            options=beautiful_color_maps,
            visible=False,
            swatch_width = 60,
        )

        self.color_map_selector.width = self.color_map_selector.height
        self.center_colormap_on_zero_tick = pn.widgets.Checkbox(
            name="Center color map on zero.", value=False
        )

        self.color_map_selector.value_name = "BuRd"
        self.color_map_selector.value = beautiful_color_maps["BuRd"]

        polygons, volume_compo_list, volume_color_list = self.compute_fn(
            (1, 0, 0), (0, 1, 0), u_min, v_min, u_max, v_max, z
        )

        self.plotter = Bokeh2DPlotter()
        self.plotter.plot_2d_frame(polygons, volume_compo_list, volume_color_list)

        if (
            slave.get_label_coloring_mode(self.field_color_selector.value[0]) == VisualizationMode.FROM_VALUE
        ):
            self.plotter.update_colorbar(
                True,
                (
                    min([float(e) for e in volume_compo_list]),
                    max([float(e) for e in volume_compo_list]),
                ),
            )
        else:
            self.plotter.update_colorbar(False, (None, None))

        fig_pane = self.plotter.make_panel()

        hide_show_button = pn.widgets.ButtonIcon(
            # margin=0,
            size="2.5em",
            icon="adjustments",
            description="Display plot tools and axis",
            visible=False,
        )

        self.fig_overlay = Overlay(
            figure=fig_pane,
            button_1=self.color_map_selector,
            button_2=hide_show_button,
            margin=0,
            width_policy="max",
            height_policy="max",
            title=pn.pane.Markdown(f"## {self.name}", visible=False),
        )

        self.borders_displayed = False

        def hide_show_axis(_):
            """Hides and shows the figure axis

            Parameters
            ----------
            _ : Any
                Button clic event
            """
            if not self.borders_displayed:
                self.plotter.display_borders(True)
                self.fig_overlay.distance_from_right = "40px"
                self.fig_overlay.distance_from_left = "40px"
                self.borders_displayed = not self.borders_displayed
            else:
                self.plotter.display_borders(False)
                self.fig_overlay.distance_from_right = "10px"
                self.fig_overlay.distance_from_left = "10px"
                self.borders_displayed = not self.borders_displayed

        hide_show_button.on_click(hide_show_axis)

        self.x0_inp = pn.widgets.FloatInput(
            name="u_min",
            value=u_min,
            start=-1e6,
            end=1e6,
            step=0.1,
            width=100,
            align="center",
        )
        self.y0_inp = pn.widgets.FloatInput(
            name="v_min",
            value=v_min,
            start=-1e6,
            end=1e6,
            step=0.1,
            width=100,
            align="center",
        )
        self.x1_inp = pn.widgets.FloatInput(
            name="u_max",
            value=u_max,
            start=-1e6,
            end=1e6,
            step=0.1,
            width=100,
            align="center",
        )
        self.y1_inp = pn.widgets.FloatInput(
            name="v_max",
            value=v_max,
            start=-1e6,
            end=1e6,
            step=0.1,
            width=100,
            align="center",
        )
        self.z_inp = pn.widgets.FloatInput(
            name="w", value=z, start=-1e6, end=1e6, step=0.1, width=100, align="center"
        )
        self.step_inp = pn.widgets.IntInput(
            name="n_rows",
            value=300,
            start=0,
            end=10000,
            step=1,
            width=100,
            align="center",
        )
        self.recompute_btn = pn.widgets.Button(
            name="Recompute", button_type="success", align="center"
        )

        if True:
            self.u0_inp = pn.widgets.FloatInput(
                name="u0", value=1, start=0, end=1, width=100
            )
            self.u1_inp = pn.widgets.FloatInput(
                name="u1", value=0, start=0, end=1, width=100
            )
            self.u2_inp = pn.widgets.FloatInput(
                name="u2", value=0, start=0, end=1, width=100
            )
            self.v0_inp = pn.widgets.FloatInput(
                name="v0", value=0, start=0, end=1, width=100
            )
            self.v1_inp = pn.widgets.FloatInput(
                name="v1", value=1, start=0, end=1, width=100
            )
            self.v2_inp = pn.widgets.FloatInput(
                name="v2", value=0, start=0, end=1, width=100
            )

            def xplus_fn(event):
                """Defines the direction vectors to Y+ and Z+

                Parameters
                ----------
                event : Any
                    Argument to make the function linkable to a button.
                """
                to_update = {"u0": 0, "u1": 1, "u2": 0, "v0": 0, "v1": 0, "v2": 1}
                self.__new_data = {**self.__new_data, **to_update}
                self.__range_to_update = True
                pn.state.curdoc.add_next_tick_callback(self.async_update_data)

            # Attach the CB to the button
            xplus = pn.widgets.Button(name="X+", button_type="success", width=50)
            xplus.on_click(xplus_fn)

            def yplus_fn(event):
                """Defines the direction vectors to X+ and Z+

                Parameters
                ----------
                event : Any
                    Argument to make the function linkable to a button.
                """
                to_update = {"u0": 1, "u1": 0, "u2": 0, "v0": 0, "v1": 0, "v2": 1}
                self.__new_data = {**self.__new_data, **to_update}
                self.__range_to_update = True
                pn.state.curdoc.add_next_tick_callback(self.async_update_data)

            # Attach the CB to the button
            yplus = pn.widgets.Button(name="Y+", button_type="success", width=50)
            yplus.on_click(yplus_fn)

            def zplus_fn(event):
                """Defines the direction vectors to X+ and Y+

                Parameters
                ----------
                event : Any
                    Argument to make the function linkable to a button.
                """
                to_update = {"u0": 1, "u1": 0, "u2": 0, "v0": 0, "v1": 1, "v2": 0}
                self.__new_data = {**self.__new_data, **to_update}
                self.__range_to_update = True
                pn.state.curdoc.add_next_tick_callback(self.async_update_data)

            # Attach the CB to the button
            zplus = pn.widgets.Button(name="Z+", button_type="success", width=50)
            zplus.on_click(zplus_fn)

            def xminus_fn(event):
                """Defines the direction vectors to Y- and Z+

                Parameters
                ----------
                event : Any
                    Argument to make the function linkable to a button.
                """
                to_update = {"u0": 0, "u1": -1, "u2": 0, "v0": 0, "v1": 0, "v2": 1}
                self.__new_data = {**self.__new_data, **to_update}
                self.__range_to_update = True
                pn.state.curdoc.add_next_tick_callback(self.async_update_data)

            # Attach the CB to the button
            xminus = pn.widgets.Button(name="X-", button_type="success", width=50)
            xminus.on_click(xminus_fn)

            def yminus_fn(event):
                """Defines the direction vectors to X- and Z+

                Parameters
                ----------
                event : Any
                    Argument to make the function linkable to a button.
                """
                to_update = {"u0": -1, "u1": 0, "u2": 0, "v0": 0, "v1": 0, "v2": 1}
                self.__new_data = {**self.__new_data, **to_update}
                self.__range_to_update = True
                pn.state.curdoc.add_next_tick_callback(self.async_update_data)

            # Attach the CB to the button
            yminus = pn.widgets.Button(name="Y-", button_type="success", width=50)
            yminus.on_click(yminus_fn)

            def zminus_fn(event):
                """Defines the direction vectors to X- and Y+

                Parameters
                ----------
                event : Any
                    Argument to make the function linkable to a button.
                """
                to_update = {"u0": -1, "u1": 0, "u2": 0, "v0": 0, "v1": 1, "v2": 0}
                self.__new_data = {**self.__new_data, **to_update}
                self.__range_to_update = True
                pn.state.curdoc.add_next_tick_callback(self.async_update_data)

            # Attach the CB to the button
            zminus = pn.widgets.Button(name="Z-", button_type="success", width=50)
            zminus.on_click(zminus_fn)

        u = pn.Column(self.u0_inp, self.u1_inp, self.u2_inp)
        v = pn.Column(self.v0_inp, self.v1_inp, self.v2_inp)

        axis_buttons = pn.Column(
            pn.Row(xplus, yplus, zplus), pn.Row(xminus, yminus, zminus)
        )

        self.axes_card = pn.Card(
                pn.Column(axis_buttons, pn.Row(u, v)),
                title="View axis coordinates",
                width=350,
                margin=(0, 0, 0, 0),
                collapsed=True,
            )
        
        file_loader_list = []
        for fi in self.file_browsers:
            file_loader_list.append(pn.pane.Markdown(f"{fi} file browser", margin=(0, 0, 0, 0)))
            file_loader_list.append(self.file_browsers[fi])

        self.side_bar = pn.layout.WidgetBox(
            # File loaders
            pn.Card(
                pn.Column(
                    *file_loader_list,
                    margin=(0, 0, 10, 10),
                ),
                title=load_files_label,
                width=350,
                margin=(0, 0, 0, 0),
                collapsed=True,
            ),
            # Color field properties
            pn.Card(
                pn.Column(
                    self.field_color_selector,
                    self.center_colormap_on_zero_tick,
                ),
                title=select_coloring_label,
                width=350,
                margin=(0, 0, 0, 0),
                collapsed=True,
            ),
            # View axis
            self.axes_card,
            # Column parameters
            max_width=350,
            sizing_mode="stretch_width",
            margin=(0, 0, 0, 0),
        )

        def ranges_cb(
            x0: float,
            x1: float,
            y0: float,
            y1: float,
        ):
            """Updates the bounds FloatInput based on the current frame zoom.

            Parameters
            ----------
            x0 : float
                Horizontal axis minimum value
            x1 : float
                Horizontal axis maximum value
            y0 : float
                Vertical axis minimum value
            y1 : float
                Vertical axis maximum value
            """
            to_update = {"x0": x0, "x1": x1, "y0": y0, "y1": y1}
            self.__new_data = {**self.__new_data, **to_update}
            self.__range_to_update = True
            pn.state.curdoc.add_next_tick_callback(self.async_update_data)

        # Attach the CB to the event
        self.plotter._set_callback_on_range_update(ranges_cb)

        def recompute_cb(event):
            """Function called on "Recompute" button clic to update the plot

            Parameters
            ----------
            event : Any
                Button clic trigering event
            """
            self.recompute()
            if pn.state.curdoc is not None:
                pn.state.curdoc.add_next_tick_callback(self.async_update_data)

        # Attach the CB to the button
        self.recompute_btn.on_click(recompute_cb)
        self.field_color_selector.param.watch(recompute_cb, "value")
        self.color_map_selector.param.watch(recompute_cb, "value_name")
        self.center_colormap_on_zero_tick.param.watch(recompute_cb, "value")

        options_widgets: List[pn.widgets.Widget] = [
            self.__get_option_widget(e) for e in slave.get_options()
        ]

        for w in options_widgets:
            if hasattr(w, "value"):
                w.param.watch(recompute_cb, "value")

        if self.geometry_type == GeometryType._2D:
            self.z_inp.visible = False
            self.axes_card.visible = False
        if not self.rasterized:
            self.step_inp.visible = False

        self.bounds_row = pn.Row(
            self.x0_inp,
            self.y0_inp,
            self.x1_inp,
            self.y1_inp,
            self.z_inp,
            self.step_inp,
            *options_widgets,
            self.recompute_btn,
            pn.pane.Markdown(f"## {self.name}", align="center"),
        )

        self.main_frame = self.fig_overlay

        self.periodic_recompute_added = False

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
                self.plotter.set_color_map(self.color_map_selector.value_name)

            # Commented as apparently not used
            # if "source_coordinates" in self.__new_data:
            #     self.source_coordinates.update(data = self.__new_data["source_coordinates"])

            if "source_polygons" in self.__new_data:
                self.current_polygons = self.__new_data["source_polygons"]
                if not self.update_polygons:
                    new_compo_name = self.polygon_worker.sort_list(
                        self.__new_data["source_polygons"][COMPO_NAMES]
                    )
                    new_color = self.polygon_worker.sort_list(
                        self.__new_data["source_polygons"][COLORS]
                    )

                    self.plotter.update_colors(
                        new_compo_name,
                        new_color,
                    )
                else:
                    self.plotter.update_2d_frame(
                        polygon_list=self.__new_data["source_polygons"][POLYGONS],
                        compo_list=self.__new_data["source_polygons"][COMPO_NAMES],
                        colors=self.__new_data["source_polygons"][COLORS],
                    )

            self.__data_to_update = False

            # this is necessary only in a notebook context where sometimes we have to force Panel/Bokeh to push an update to the browser
            pn.io.push_notebook(self.fig_overlay)

            if profile_time:
                print(f"Async function : {time.time() - st}")

        if self.__range_to_update:
            if "u0" in self.__new_data:
                self.u0_inp.value = self.__new_data["u0"]
            if "u1" in self.__new_data:
                self.u1_inp.value = self.__new_data["u1"]
            if "u2" in self.__new_data:
                self.u2_inp.value = self.__new_data["u2"]

            if "v0" in self.__new_data:
                self.v0_inp.value = self.__new_data["v0"]
            if "v1" in self.__new_data:
                self.v1_inp.value = self.__new_data["v1"]
            if "v2" in self.__new_data:
                self.v2_inp.value = self.__new_data["v2"]

            if "x0" in self.__new_data:
                self.x0_inp.value = self.__new_data["x0"]
            if "y0" in self.__new_data:
                self.y0_inp.value = self.__new_data["y0"]
            if "x1" in self.__new_data:
                self.x1_inp.value = self.__new_data["x1"]
            if "y1" in self.__new_data:
                self.y1_inp.value = self.__new_data["y1"]

            self.__range_to_update = False

            # this is necessary only in a notebook context where sometimes we have to force Panel/Bokeh to push an update to the browser
            pn.io.push_notebook(self.fig_overlay)

        self.__new_data = {}

    def compute_fn(
        self,
        u: Tuple[float, float, float],
        v: Tuple[float, float, float],
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        z: float,
        res_x: int = 300,
        res_y: int = 300,
    ) -> Tuple[
        List[PolygonElement],
        List[Union[str, int]],
        List[str],
        List[Tuple[int, int, int]],
    ]:
        """Request the slave to compute a new frame, and updates the polygons to display

        Parameters
        ----------
        u : Tuple[float, float, float]
            Direction vector along the horizontal axis
        v : Tuple[float, float, float]
            Direction vector along the vertical axis
        x0 : float
            Lower bound value along the u axis
        y0 : float
            Lower bound value along the v axis
        x1 : float
            Upper bound value along the u axis
        y1 : float
            Upper bound value along the v axis
        z : float
            Value along the u ^ v axis
        res_x : int, optional
            Number of points along the X axis, if applicable, by default 300
        res_y : int, optional
            Number of points along the Y axis, if applicable, by default 300

        Returns
        -------
        List[PolygonElement], List[Union[str, int]], List[str], List[Tuple[int, int, int]]
            Formatted list of polygons, list of volumes, list of compositions, list of volume colors.
        """
        if self.bounds_row is None:
            options = {
                e.name: e.default
                for e in self.slave.get_options()
                if hasattr(e, "default")
            }
        else:
            options = {
                e.name: e.value for e in self.bounds_row.objects if hasattr(e, "value")
            }

        if len(self.field_color_selector.value) > 0:
            computed_data = self.slave.compute_2D_data(
                u,
                v,
                x0,
                x1,
                y0,
                y1,
                res_x,
                res_y,
                z,
                self.field_color_selector.value[0],
                self.color_map_selector.value_name,
                self.center_colormap_on_zero_tick.value,
                options,
            )

            if computed_data is None:
                print(
                    f"\n\n Got None from computed data on {self.name}, returning the past values.\n\n"
                )
                return (
                    self.current_polygons[POLYGONS],
                    self.current_polygons[COMPO_NAMES],
                    self.current_polygons[COLORS],
                )
            polygon_list, dict_compos_found, dict_volume_color, polygons_updated = (
                computed_data
            )
            self.update_polygons = polygons_updated

            return self.polygon_worker.sort_polygon_list(
                polygon_list,
                dict_compos_found,
                dict_volume_color,
                sort=polygons_updated,
            )
        else:
            return None, None, None

    def recompute(
        self,
    ):
        """Recomputes the figure based on the new bounds and parameters.

        Parameters
        ----------
        event : Any
            Event to make the function linkable to a button
        """
        self.recompute_btn.disabled = True
        if profile_time:
            st = time.time()
        x0 = self.x0_inp.value
        y0 = self.y0_inp.value
        x1 = self.x1_inp.value
        y1 = self.y1_inp.value
        steps = self.step_inp.value

        res_x, res_y = self.plotter.get_resolution()

        if res_x is None:
            res_x = steps
            res_y = steps

        elif steps < res_y:
            res_x = int(steps * res_x / res_y)
            res_y = steps

        print(f"{self.name} - Recomputing for range : ({x0}, {y0}), ({x1}, {y1})")

        def get_uv() -> Tuple[np.ndarray, np.ndarray]:
            """Gets the normal direction vectors from the FloatInput objects.

            Returns
            -------
            Tuple[np.ndarray, np.ndarray]
                Vectors U, V
            """
            u0 = self.u0_inp.value
            u1 = self.u1_inp.value
            u2 = self.u2_inp.value
            v0 = self.v0_inp.value
            v1 = self.v1_inp.value
            v2 = self.v2_inp.value

            u = np.array([u0, u1, u2])
            v = np.array([v0, v1, v2])

            u = u / np.linalg.norm(u)
            v = v / np.linalg.norm(v)

            return u, v

        # num_levels = num_levels_inp.value
        u, v = get_uv()

        polygons, volume_compo_list, volume_color_list = self.compute_fn(
            u, v, x0, y0, x1, y1, self.z_inp.value, res_x=res_x, res_y=res_y
        )

        if polygons is not None:
            if profile_time:
                print(f"Plot panel compute function : {time.time() - st}")
                st = time.time()

            self.__new_data = {
                # Commented as apparently not used
                # "source_coordinates" : {
                #                             "u_min" : [x0],
                #                             "v_min" : [y0],
                #                             "dw" : [x1 - x0],
                #                             "dh" : [y1 - y0],
                #                             "u0" : [u[0]],
                #                             "u1" : [u[1]],
                #                             "u2" : [u[2]],
                #                             "v0" : [v[0]],
                #                             "v1" : [v[1]],
                #                             "v2" : [v[2]],
                #                             "w0" : [w[0]],
                #                             "w1" : [w[1]],
                #                             "w2" : [w[2]],
                #                             "w" : [z0],
                #                         },
                "source_polygons": {
                    POLYGONS: polygons,
                    COLORS: volume_color_list,
                    VOLUME_NAMES: [p.volume_id for p in polygons],
                    COMPO_NAMES: volume_compo_list,
                },
            }

            if (
                len(self.field_color_selector.value) > 0
                and self.slave.get_label_coloring_mode(self.field_color_selector.value[0]) == VisualizationMode.FROM_VALUE
            ):
                self.__new_data["color_mapper"] = {
                    "new_low": np.array(volume_compo_list).astype(float).min(),
                    "new_high": np.array(volume_compo_list).astype(float).max(),
                }
                self.__new_data["hide_colorbar"] = False
            else:
                self.__new_data["hide_colorbar"] = True

            self.__data_to_update = True

            if profile_time:
                print(f"Plot panel preparing data : {time.time() - st}")

            self.recompute_btn.disabled = False

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

        new_index = self.copy_index = 1

        if keep_name:
            new_name = self.name
        else:
            if new_index == 1:
                new_name = f"{self.name} - 2"
            else:
                new_name = self.name.replace(
                    f" - {new_index + 1}", f" - {new_index + 2}"
                )

        new_visualiser = VisualizationPanel(self.slave, new_name)
        new_visualiser.copy_index = new_index

        new_visualiser.plotter.source_polygons.data = self.plotter.source_polygons.data.copy()
        # new_visualiser.source_coordinates.data = self.source_coordinates.data.copy()

        return new_visualiser

    def __get_option_widget(self, option: OptionElement) -> pn.widgets.Widget:
        """Returns the widget associated to a Option element

        Parameters
        ----------
        option : OptionElement
            Parameters that define the requested widget.

        Returns
        -------
        pn.widgets.Widget
            Input widget

        Raises
        ------
        ValueError
            The requested option type is not implemented.
        """
        if option.option_type == bool:
            return pn.widgets.Checkbox(
                name=option.name,
                value=option.default,
                align="center",
                styles={"font-size": "16px"},
            )  # , description=option.description)
        elif option.option_type == float:
            return pn.widgets.FloatInput(
                name=option.name,
                value=option.default,
                description=option.description,
                align="center",
                width=100,
            )
        elif option.option_type == int:
            return pn.widgets.IntInput(
                name=option.name,
                value=option.default,
                description=option.description,
                align="center",
                width=100,
            )
        elif option.option_type == str:
            return pn.widgets.TextInput(
                name=option.name,
                value=option.default,
                description=option.description,
                align="center",
                width=100,
            )
        else:
            raise ValueError(
                f"Given option type not implemented, found : {option.option_type}"
            )

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
