from typing import Callable, Dict, List, Tuple, Union
import panel as pn
import os
import pandas as pd
from scivianna.components.overlay_component import Overlay

from scivianna.enums import UpdateEvent
from scivianna.plotter_1d.bokeh_1d_plotter import BokehPlotter1D
from scivianna.slave import ComputeSlave


class LineVisualisationPanel:
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

    name: str
    """ Panel name
    """
    plotter: BokehPlotter1D
    """ 1D plotter displaying and updating the graph
    """
    update_event: Union[UpdateEvent, List[UpdateEvent]] = UpdateEvent.RECOMPUTE
    """ On what event does the panel recompute itself
    """
    sync_field: bool = False
    """ On what event does the panel recompute itself
    """

    position: Tuple[float, float, float] = None
    """Position where request the plot"""
    volume_id: str = None
    """Volume ID where request the plot"""

    def __init__(
            self,
            slave: ComputeSlave,
            name: str = "",
        ):
        """Visualization panel constructor

        Parameters
        ----------
        slave : ComputeSlave
            Slave used to take the information from.
        name : str
            Name of the panel.
        """
        print("New frame built with name ", name)
        self.name = name
        self.copy_index = 0
        
        self.slave = slave
        self.fields = self.slave.get_label_list()

        self.bounds_row = None

        self.__data_to_update: bool = False
        """Is it required to update the data, can be set on periodic event or on clic"""
        self.field_change_callback: Callable = None
        """Function to call when the field is changed"""

        self.current_time = 0.0
        self.current_value = None

        self.series: Dict[str, pd.Series] = {}

        def recompute_cb(event):
            self.recompute()
            
            if pn.state.curdoc is not None:
                pn.state.curdoc.add_next_tick_callback(self.async_update_data)

        def field_changed(event):
            """Function called on field changed

            Parameters
            ----------
            event : Any
                Field changed trigering event
            """
            if self.field_change_callback is not None and\
                    len(self.field_color_selector.value) > 0:
                self.field_change_callback(self.field_color_selector.value[0])
            recompute_cb(event)

        fields_list = self.slave.get_label_list()
        self.field_color_selector = pn.widgets.MultiChoice(
            name="Color field",
            options=fields_list,
            value=[fields_list[0]],
        )
        self.field_color_selector.param.watch(field_changed, "value")

        self.__new_data = {}

        self.plotter = BokehPlotter1D()
        self.__get_series(self.field_color_selector.value[0])
        self.async_update_data()
        self.plotter.set_visible(self.field_color_selector.value)

        fig_pane = self.plotter.make_panel()

        self.fig_overlay = Overlay(
            figure=fig_pane,
            message=pn.pane.Markdown(""),
            margin=0,
            width_policy="max",
            height_policy="max",
            title=pn.pane.Markdown(f"## {self.name}", visible=False),
        )

        self.side_bar = pn.layout.WidgetBox(
            self.field_color_selector,
            # Column parameters
            max_width=350,
            sizing_mode="stretch_width",
            margin=(0, 0, 0, 0),
        )

        self.bounds_row = pn.Row(pn.pane.Markdown(f"## {self.name}", align="center"))

        self.main_frame = self.fig_overlay

        self.periodic_recompute_added = False

    @pn.io.hold()
    def async_update_data(
        self,
    ):
        """Update the figures and buttons based on what was added in self.__new_data. This function is called between two servers ticks to prevent multi-users collisions."""
        
        if "field_names" in self.__new_data:
            self.__data_to_update = False
            
            self.field_color_selector.value = self.__new_data["field_names"]
            self.__new_data = {}
            self.async_update_data()

        elif self.__data_to_update:
            for key in self.series:
                if self.series[key] is not None:
                    # Can be None if the async happens at the same time as the next recompute
                    self.plotter.update_plot(key, self.series[key])

            self.plotter.set_visible(list(self.series.keys()))

            self.__data_to_update = False

            # this is necessary only in a notebook context where sometimes we have to force Panel/Bokeh to push an update to the browser
            pn.io.push_notebook(self.fig_overlay)

    def recompute(
        self,
    ):
        """Recomputes the figure based on the new bounds and parameters.

        Parameters
        ----------
        event : Any
            Event to make the function linkable to a button
        """

        if len(self.field_color_selector.value) > 0:
            self.__data_to_update = True

            self.series.clear()
            for key in self.field_color_selector.value:
                self.__get_series(key)

            if pn.state.curdoc is not None:
                pn.state.curdoc.add_next_tick_callback(self.async_update_data)

    def __get_series(self, key: str):
        """Get the serie or series associated to the given key

        Parameters
        ----------
        key : str
            Field to request to the slave
        """
        series = self.slave.get_1D_value(self.position, self.volume_id, None, key)

        if isinstance(series, list):
            for serie in series:
                self.series[serie.name] = serie
        else:
            self.series[series.name] = series

    def duplicate(self, keep_name: bool = False) -> "LineVisualisationPanel":
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

        new_visualiser = LineVisualisationPanel(new_name)
        new_visualiser.copy_index = new_index

        return new_visualiser

    def get_slave(
        self,
    ):
        return self.slave

    def recompute_at(self, position: Tuple[float, float, float], volume_id: str):
        """Triggers a panel recomputation at the provided location. Called by layout update event.

        Parameters
        ----------
        position : Tuple[float, float, float]
            Location to provide to the slave
        volume_id : str
            Volume id to provide to the slave
        """
        self.fig_overlay.show_temporary_message(f"Updating for position {position} and cell {volume_id}", 1000)
        self.position = position
        self.volume_id = volume_id
        self.recompute()

    def set_field(self, field_names: List[str], allow_wrong_name: bool = False):
        """Updates the plotted fields

        Parameters
        ----------
        field_name : List[str]
            Fields to display
        allow_wrong_name : bool
            Accept a wrong field (nothing happens)
        """
        fields: List[str] = []
        if isinstance(field_names, list):
            for field_name in field_names:
                if field_name not in self.field_color_selector.options:
                    if allow_wrong_name:
                        continue
                    else:
                        raise ValueError(f"Requested field {field_name} not found, available fields : {self.field_color_selector.options}")
                else:
                    fields.append(field_name)
        else:
            if field_names not in self.field_color_selector.options:
                if allow_wrong_name:
                    pass
                else:
                    raise ValueError(f"Requested field {field_names} not found, available fields : {self.field_color_selector.options}")
            else:
                fields.append(field_names)

        if fields != [] and set(fields) != set(self.field_color_selector.value):
            self.__new_data["field_names"] = fields

            self.__data_to_update = True
            if pn.state.curdoc is not None:
                pn.state.curdoc.add_next_tick_callback(self.async_update_data)

    def provide_field_change_callback(self, callback: Callable):
        """Stores a function to call everytime the displayed field is changed.
        the functions takes a string as argument.

        Parameters
        ----------
        callback : Callable
            Function to call.
        """
        self.field_change_callback = callback
