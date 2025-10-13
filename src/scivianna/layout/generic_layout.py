import functools
import panel as pn
from typing import Callable, Dict, List, Tuple, Type, Union

from bokeh.plotting import curdoc

from scivianna.enums import UpdateEvent
from scivianna.interface.generic_interface import GenericInterface
from scivianna.slave import ComputeSlave
from scivianna.panel.plot_panel import VisualizationPanel
from scivianna.panel.line_plot_panel import LineVisualisationPanel
from scivianna.utils.interface_tools import (
    GenericInterfaceEnum,
    get_interface_default_panel,
    load_available_interfaces,
)
from scivianna.panel.styles import card_style


class GenericLayout:
    """Displayable that lets arranging several VisualizationPanel"""

    side_bar: pn.Column
    """ Side bar containing the options of the grid stack and of the active panel
    """
    bounds_row: pn.Row
    """ Bounds row of the active panel
    """
    main_frame: pn.Column
    """ Main frame : gridstack of different VisualizationPanel main_frame
    """

    available_interfaces: Dict[Union[str, GenericInterfaceEnum], Type[GenericInterface]]
    """ Available interface classes to switch from one to another
    """
    load_available_interfaces: Callable = None
    """ Function loading available interfaces. Can be overwriten to add additional interfaces.
    """

    visualisation_panels: Dict[str, VisualizationPanel]
    """ Dictionnary containing all visualisation panels.
    """

    def __init__(
        self,
        visualisation_panels: Dict[str, VisualizationPanel],
        additional_interfaces: Dict[
            Union[str, GenericInterfaceEnum], Type[GenericInterface]
        ] = {},
        add_run_button: bool = False,
    ):
        self.visualisation_panels = visualisation_panels

        if self.load_available_interfaces is None:
            self.available_interfaces = load_available_interfaces()
        else:
            self.available_interfaces = self.load_available_interfaces()

        for interface in additional_interfaces:
            if not issubclass(additional_interfaces[interface], GenericInterface):
                raise TypeError(
                    f"Provided interface {interface} is not a GenericInterface, found type {type(additional_interfaces[interface])}"
                )
            self.available_interfaces[interface] = additional_interfaces[interface]

        self.interface_selector = pn.widgets.Select(
            name="Code",
            options=[
                val.value if isinstance(val, GenericInterfaceEnum) else str(val)
                for val in self.available_interfaces.keys()
            ],
        )

        """
            Current edited frame selector
        """
        self.frame_selector = pn.widgets.Select(
            name="Visualizer selector",
            options=list(self.visualisation_panels.keys()),
            value=list(self.visualisation_panels.keys())[0],
        )

        self.code_interface_to_update = True
        self.interface_selector.param.watch(self.change_code_interface, "value")

        self.frame_selector.param.watch(self.change_current_frame, "value")

        """
            Adding a button to the overlays to switch to the frame
        """
        for key in self.visualisation_panels:
            self.visualisation_panels[key].fig_overlay.button_3 = self._make_button_icon()
            self.visualisation_panels[key].fig_overlay.button_3.on_click(functools.partial(self.set_to_frame, frame_name=key))

            if hasattr(self.visualisation_panels[key].bounds_row[0], "value"):
                self.visualisation_panels[key].bounds_row[0].param.watch(
                    functools.partial(self.set_to_frame, frame_name=key), "value"
                )

        """
            ButtonIcon to split the frames
            List of available icons : https://tabler.io/icons

            border-vertical / border-horizontal
            box-align-left / box-align-right
            columns-2 / column-insert-right
            layout-rows / row-insert-bottom
        """

        self.duplicate_horizontally_button = pn.widgets.ButtonIcon(
            icon="columns-2", description="Duplicate horizontally", height=30, width=30
        )
        self.duplicate_vertitally_button = pn.widgets.ButtonIcon(
            icon="layout-rows", description="Duplicate vertically", height=30, width=30
        )
        self.split_new_horizontally_button = pn.widgets.ButtonIcon(
            icon="column-insert-right",
            description="Split horizontally",
            height=30,
            width=30,
        )
        self.split_new_vertically_button = pn.widgets.ButtonIcon(
            icon="row-insert-bottom",
            description="Split vertically",
            height=30,
            width=30,
        )

        def duplicate_vertically(event: bool):
            """Split the panel vertically, the new panel is a copy of the first

            Parameters
            ----------
            event : bool
                If the call is from a button press or release
            """
            if event:
                self.duplicate(True)

        def duplicate_hozironally(event: bool):
            """Split the panel hozironally, the new panel is a copy of the first

            Parameters
            ----------
            event : bool
                If the call is from a button press or release
            """
            if event:
                self.duplicate(False)

        self.duplicate_horizontally_button.on_click(duplicate_hozironally)
        self.duplicate_vertitally_button.on_click(duplicate_vertically)

        def request_recompute(event):
            """Request a recompute task on all panels, which will trigger the addition of a periodict update on the panels

            Parameters
            ----------
            event : bool
                If the call is from a button press or release
            """
            if event:
                # for panel in self.visualisation_panels:
                #     self.visualisation_panels[panel].add_periodic_update()
                if self.periodic_recompute_added:
                    self.run_button.icon = "player-play"
                    self.stop_periodic_update()
                else:
                    self.run_button.icon = "player-pause"
                    self.add_periodic_update()

        #   Adding a play button at the beginning of the side bar
        #   It will trigger a periodic task to update the plot in case of code coupling simulation
        self.periodic_recompute_added = False
        if add_run_button:
            self.run_button = pn.widgets.ButtonIcon(
                icon="player-play",
                description="Start automatic update",
                height=30,
                width=30,
                align="center",
            )
            self.run_button.on_click(request_recompute)

            self.curdoc = curdoc()

            # Apparently not necessary, and breaks the gridstack split, so bye bye...
            # self.curdoc.add_root(self.fig)

            pn.state.curdoc = self.curdoc
        else:
            self.run_button = None

        self.layout_param_card = pn.Card(
            self.frame_selector,
            self.interface_selector,
            pn.Row(
                self.duplicate_horizontally_button, self.duplicate_vertitally_button
            ),
            width=350,
            title="Arrangement parameters",
            margin=0,
            styles=card_style,
        )

        self.panel_param_cards = {
            frame.name: pn.Card(
                frame.side_bar,
                width=350,
                margin=0,
                styles=card_style,
                title=f"{frame.name} parameters",
            )
            for frame in self.visualisation_panels.values()
        }

        self.side_bar = pn.Column(
            self.layout_param_card,
            *self.panel_param_cards.values(),
            margin=-10,
            width=350,
        )
        self.bounds_row = pn.Row(
            *[frame.bounds_row for frame in self.visualisation_panels.values()]
        )

        if self.run_button is not None:
            self.bounds_row.insert(0, self.run_button)

        self.change_current_frame(None)

        self.panels_to_recompute: List[str] = []

        for panel in self.visualisation_panels.values():
            if isinstance(panel, VisualizationPanel):
                panel.provide_on_clic_callback(self.on_clic_callback)
                panel.provide_on_mouse_move_callback(self.mouse_move_callback)
                panel.provide_field_change_callback(self.field_change_callback)
            elif isinstance(panel, LineVisualisationPanel):
                panel.provide_field_change_callback(self.field_change_callback)

        self.last_hover_id = None
        """Last hovered cell to trigger change if applicable"""

    @pn.io.hold()
    def change_code_interface(self, event):
        """Replaces the panel to one linked to the code interface

        Parameters
        ----------
        event : Any
            Event to make the function linkable to the gridstack
        """
        current_interface = self.interface_selector.value
        current_frame = self.frame_selector.value
        interface_enum = list(self.available_interfaces.keys())[
            self.interface_selector.values.index(self.interface_selector.value)
        ]

        if (
            self.code_interface_to_update
            and self.available_interfaces[interface_enum] != self.visualisation_panels[current_frame].slave.code_interface
        ):
            print(
                f"Updating code interface of panel {current_frame} to {current_interface}"
            )

            default_panel = get_interface_default_panel(
                interface_enum, title=current_frame
            )

            if default_panel is None:
                # Means the panel is custom and was provided by the user
                new_slave = ComputeSlave(self.available_interfaces[interface_enum])

                self.visualisation_panels[current_frame] = VisualizationPanel(
                    slave=new_slave, name=current_frame
                )
            else:
                self.visualisation_panels[current_frame] = default_panel

            self.visualisation_panels[current_frame].fig_overlay.button_3 = self._make_button_icon()
            self.visualisation_panels[current_frame].fig_overlay.button_3.on_click(functools.partial(self.set_to_frame, frame_name=current_frame))

            self.visualisation_panels[current_frame].provide_on_clic_callback(self.on_clic_callback)
            self.visualisation_panels[current_frame].provide_on_mouse_move_callback(self.mouse_move_callback)

            self.visualisation_panels[current_frame].bounds_row[0].param.watch(
                functools.partial(self.set_to_frame, frame_name=current_frame), "value"
            )

    def change_current_frame(self, event):
        """Swap the the active panel

        Parameters
        ----------
        event : Any
            Event to make the function linkable to the gridstack
        """
        current_frame = self.frame_selector.value

        print("Changing to ", current_frame)

        for frame in self.panel_param_cards:
            self.panel_param_cards[frame].visible = frame == current_frame
            self.visualisation_panels[frame].bounds_row.visible = (
                frame == current_frame
            )

    @pn.io.hold()
    def set_to_frame(self, event, frame_name: str):
        """Updates the Select widget to the active panel

        Parameters
        ----------
        event : Any
            Event to make the function linkable to the gridstack
        frame_name : str
            Name of the active panel

        Raises
        ------
        ValueError
            The provided name is not in the Select options
        """
        if frame_name in self.frame_selector.options:
            self.code_interface_to_update = False

            frame_code_enum = list(self.available_interfaces.keys())[
                list(self.available_interfaces.values()).index(
                    self.visualisation_panels[frame_name].slave.code_interface
                )
            ]

            self.interface_selector.value = (
                frame_code_enum.value
                if isinstance(frame_code_enum, GenericInterfaceEnum)
                else str(frame_code_enum)
            )

            self.frame_selector.value = frame_name
            self.code_interface_to_update = True
        else:
            raise ValueError(
                f"Frame {frame_name} not in options, available keys : {self.frame_selector.options}"
            )

    def duplicate(self, horizontal: bool):
        """Split the panel, the new panel is a copy of the first, all panels are duplicated.

        Parameters
        ----------
        horizontal : bool
            Whether the cut should be horizontal or vertical
        """
        raise NotImplementedError()

    def get_panel(self, panel_name: str) -> VisualizationPanel:
        """Returns the VisualizationPanel associated to the given name

        Parameters
        ----------
        panel_name : str
            Name of the panel

        Returns
        -------
        VisualizationPanel
            Requested panel

        Raises
        ------
        ValueError
            No panel at the given name
        """
        if panel_name not in self.visualisation_panels:
            raise ValueError(
                f"Unknown panel requested: {panel_name}, available panels: {list(self.visualisation_panels.keys())}. Make sure the key requested by the exchanger is defined as panel_name@field_name"
            )

        return self.visualisation_panels[panel_name]

    def set_panel(self, panel_name: str, panel: VisualizationPanel):
        """Updates the VisualizationPanel associated to the given name

        Parameters
        ----------
        panel_name : str
            Name of the panel
        panel:VisualizationPanel
            New panel value
        """
        self.visualisation_panels[panel_name] = panel

    def stop_periodic_update(
        self,
    ):
        """Stops the curdoc a periodic task (every 100 ms) to automatically update the plots."""
        self.periodic_recompute_added = False
        pn.state.curdoc.add_timeout_callback(self.recompute, 100)

    def add_periodic_update(
        self,
    ):
        """Add to the curdoc a periodic task (every 100 ms) to automatically update the plots."""
        self.periodic_recompute_added = True
        pn.state.curdoc.add_timeout_callback(self.recompute, 100)

    def recompute(
        self,
    ):
        """Periodically called function that requests calling async_update_data at the end of current tick."""
        if pn.state.curdoc is not None:
            pn.state.curdoc.add_next_tick_callback(self.async_update_data)

    @pn.io.hold()
    async def async_update_data(
        self,
    ):
        """Request all panels to update themselves. This function being called between two ticks, it will not trigger collisions between automatic and user update requests."""
        for panel in self.panels_to_recompute:
            self.visualisation_panels[panel].recompute()
            self.visualisation_panels[panel].async_update_data()
        self.panels_to_recompute.clear()
        if self.periodic_recompute_added:
            self.add_periodic_update()

    def mark_to_recompute(self, panels_to_recompute):
        self.panels_to_recompute = panels_to_recompute

    def _make_button_icon(self,) -> pn.widgets.ButtonIcon:
        """Makes a button icon to switch to current panel

        Returns
        -------
        pn.widgets.ButtonIcon
            ButtonIcon
        """
        return pn.widgets.ButtonIcon(
            size="2.5em",
            icon="layout-sidebar",
            visible=False,
            description="Change side bar and coordinate bar to current plot."
        )

    def get_bounds_row(self, ) -> pn.Row:
        """Makes the layout bounds_row, if the run button exists, it will be added to the row.

        Returns
        -------
        pn.Row
            Widget row
        """

        if self.run_button is not None:
            return pn.Row(self.run_button, *[e.bounds_row for e in self.visualisation_panels.values()])
        else:
            return pn.Row(*[e.bounds_row for e in self.visualisation_panels.values()])

    def on_clic_callback(self, position: Tuple[float, float, float], volume_id: str):
        """Function calling panels update on mouse clic in a 2D panel

        Parameters
        ----------
        position : Tuple[float, float, float]
            Clic location
        volume_id : str
            Clic volume ID
        """
        for panel in self.visualisation_panels.values():
            if panel.update_event == UpdateEvent.CLIC or (isinstance(panel.update_event, list) and UpdateEvent.CLIC in panel.update_event):
                panel.recompute_at(position, volume_id)

    def mouse_move_callback(self, position: Tuple[float, float, float], volume_id: str):
        """Function calling panels update on mouse move in a 2D panel

        Parameters
        ----------
        position : Tuple[float, float, float]
            Mouse hovered location
        volume_id : str
            Move hovered volume id
        """
        for panel in self.visualisation_panels.values():
            if panel.update_event == UpdateEvent.MOUSE_POSITION_CHANGE or (isinstance(panel.update_event, list) and UpdateEvent.MOUSE_POSITION_CHANGE in panel.update_event):
                panel.recompute_at(position, volume_id)

            if volume_id != self.last_hover_id and\
                    (
                        panel.update_event == UpdateEvent.MOUSE_CELL_CHANGE
                        or (isinstance(panel.update_event, list) and UpdateEvent.MOUSE_CELL_CHANGE in panel.update_event)
                    ):
                self.last_hover_id = volume_id
                panel.recompute_at(position, volume_id)

    def field_change_callback(self, new_field: str):
        """Function calling panels update a field change

        Parameters
        ----------
        new_field : str
            New field to set
        """
        for panel in self.visualisation_panels.values():
            if panel.sync_field:
                panel.set_field(new_field, allow_wrong_name=True)
