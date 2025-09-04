import functools
from typing import Dict, List, Tuple, Type, Union
import panel as pn
import holoviews as hv

from scivianna.interface.generic_interface import GenericInterface
from scivianna.layout.generic_layout import GenericLayout
from scivianna.panel.plot_panel import ComputeSlave, VisualizationPanel
from scivianna.panel.styles import card_style
from scivianna.utils.interface_tools import (
    GenericInterfaceEnum,
)
from scivianna.components.gridstack_component import CustomGridStack

pn.extension()
hv.extension("bokeh")


class GridStackLayout(GenericLayout):
    """Displayable that lets arranging several VisualizationPanel"""

    visualisation_panels: Dict[str, VisualizationPanel]
    """ Name - VisualizationPanel dictionnary
    """
    bounds_x: Dict[str, List[int]]
    """ Name - position in the gridstack along the horizontal axis dictionnary
    """
    bounds_y: Dict[str, List[int]]
    """ Name - position in the gridstack along the vertical axis dictionnary
    """

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

    def __init__(
        self,
        visualisation_panels: Dict[str, VisualizationPanel],
        bounds_x: Dict[str, Tuple[int]],
        bounds_y: Dict[str, Tuple[int]],
        additional_interfaces: Dict[
            Union[str, GenericInterfaceEnum], Type[GenericInterface]
        ] = {},
        add_run_button: bool = False,
    ):
        """VisualizationGridStack constructor

        Parameters
        ----------
        visualisation_panels : Dict[str, VisualizationPanel]
            Dictionnary containing the VisualizationPanels
        bounds_x : Dict[str, Tuple[int]]
            Dictionnary containing position in the gridstack along the horizontal axis
        bounds_y : Dict[str, Tuple[int]]
            Dictionnary containing position in the gridstack along the vertical axis
        add_run_button:bool = False
            Add a run button to add an automatic update of the frames in the case of visualizer coupling.

        Raises
        ------
        TypeError
            One of the additional interfaces classes does not inherit from GenericInterface
        """
        assert set(bounds_x.keys()) == set(visualisation_panels.keys())
        assert set(bounds_y.keys()) == set(visualisation_panels.keys())

        self.bounds_x = bounds_x
        self.bounds_y = bounds_y

        super().__init__(visualisation_panels, additional_interfaces, add_run_button)

        size_x = max(max([x_range for x_range in bounds_x.values()]))
        size_y = max(max([y_range for y_range in bounds_y.values()]))

        size_x = max(1, size_x)
        size_y = max(1, size_y)


        """
            Allow resize frames check box
        """
        self.allow_resize_box = pn.widgets.Checkbox(
            name="Allow frames resize", value=False
        )

        def enable_disable_resize(event):
            self.enable_disable_pan()

        self.allow_resize_box.param.watch(enable_disable_resize, "value")



        """
            Building interface
        """
        self.main_frame = pn.Column(
            CustomGridStack(height_policy="max", width_policy="max", allow_resize=True),
            height_policy="max",
            width_policy="max",
            margin=0,
        )

        self.make_grid_stack()
        self.enable_disable_pan()

        self.layout_param_card.objects.append(self.allow_resize_box)


    @pn.io.hold()
    def change_code_interface(self, event):
        super().change_code_interface(event)
    
        self.make_grid_stack()
        self.change_current_frame(None)

    @pn.io.hold()
    def change_current_frame(self, event):
        """Swap the the active panel

        Parameters
        ----------
        event : Any
            Event to make the function linkable to the gridstack
        """
        super().change_current_frame(event)
        current_frame = self.frame_selector.value
        if self.bounds_x[current_frame][1] - self.bounds_x[current_frame][0] > 1:
            self.duplicate_horizontally_button.disabled = False
        else:
            self.duplicate_horizontally_button.disabled = True

        if self.bounds_y[current_frame][1] - self.bounds_y[current_frame][0] > 1:
            self.duplicate_horizontally_button.disabled = False
        else:
            self.duplicate_horizontally_button.disabled = True

    def get_grid(self) -> CustomGridStack:
        """Returns the gridstack object

        Returns
        -------
        GridStack
            Currently displayed gridstack
        """
        return self.main_frame.objects[-1]

    def enable_disable_pan(self):
        """Enable - disable figure panning"""
        if self.allow_resize_box.value:
            self.disable_figures_pan()
        else:
            self.enable_figures_pan()

        grid = self.get_grid()
        grid.allow_resize = True  # self.allow_resize_box.value
        grid.allow_drag = self.allow_resize_box.value

    def make_grid_stack(self):
        """Updates the displayed gridstack object (called after a panel split/delete)"""

        size_x = max(max([x_range for x_range in self.bounds_x.values()]))
        size_y = max(max([y_range for y_range in self.bounds_y.values()]))

        size_x = max(1, size_x)
        size_y = max(1, size_y)

        self.get_grid().clear_objects()

        for element in self.visualisation_panels:
            #  As disgusting as it looks, sleeping here helps the python to sychronize with the Javascript while splitting and avoir throwing an error

            print(
                f"Adding object {element} : {self.visualisation_panels[element].main_frame.name} - {id(self.visualisation_panels[element].main_frame)}"
            )
            if len(self.bounds_x[element]) == 0 and len(self.bounds_y[element]) == 0:
                self.get_grid()[:, :] = self.visualisation_panels[element].main_frame
                self.get_grid().add_object(
                    self.visualisation_panels[element].main_frame,
                    (0, size_x),
                    (0, size_y),
                )

            elif len(self.bounds_x[element]) == 0:
                self.get_grid()[
                    self.bounds_y[element][0]: self.bounds_y[element][1], :
                ] = self.visualisation_panels[element].main_frame
                self.get_grid().add_object(
                    self.visualisation_panels[element].main_frame,
                    (self.bounds_y[element][0], self.bounds_y[element][1]),
                    (0, size_y),
                )

            elif len(self.bounds_y[element]) == 0:
                self.get_grid()[
                    :, self.bounds_x[element][0]: self.bounds_x[element][1]
                ] = self.visualisation_panels[element].main_frame
                self.get_grid().add_object(
                    self.visualisation_panels[element].main_frame,
                    (0, size_x),
                    (self.bounds_x[element][0], self.bounds_x[element][1]),
                )

            else:
                self.get_grid()[
                    self.bounds_y[element][0]: self.bounds_y[element][1],
                    self.bounds_x[element][0]: self.bounds_x[element][1],
                ] = self.visualisation_panels[element].main_frame
                self.get_grid().add_object(
                    self.visualisation_panels[element].main_frame,
                    (self.bounds_y[element][0], self.bounds_y[element][1]),
                    (self.bounds_x[element][0], self.bounds_x[element][1]),
                )

        self.enable_disable_pan()
        self.side_bar.objects = [self.layout_param_card,
            *self.panel_param_cards.values()]
            
        self.bounds_row.objects = self.get_bounds_row().objects
    

    def disable_figures_pan(self):
        """Disable all figures pan"""
        for component in self.visualisation_panels:
            self.visualisation_panels[component].plotter._disable_interactions(True)

    def enable_figures_pan(self):
        """Enable all figures pan"""
        for component in self.visualisation_panels:
            self.visualisation_panels[component].plotter._disable_interactions(False)

    @pn.io.hold()
    def duplicate(self, horizontal: bool):
        """Split the panel, the new panel is a copy of the first, all panels are duplicated.

        Parameters
        ----------
        horizontal : bool
            Whether the cut should be horizontal or vertical
        """
        current_frame = self.frame_selector.value
        if horizontal:
            cut_possible = (
                self.bounds_y[current_frame][1] - self.bounds_y[current_frame][0] > 1
            )
        else:
            cut_possible = (
                self.bounds_x[current_frame][1] - self.bounds_x[current_frame][0] > 1
            )

        if cut_possible:
            new_visualisation_panels:Dict[str, VisualizationPanel] = {}

            old_x_min = self.bounds_x[current_frame][0]
            old_x_max = self.bounds_x[current_frame][1]
            old_y_min = self.bounds_y[current_frame][0]
            old_y_max = self.bounds_y[current_frame][1]

            if horizontal:
                cut_coordinate = int(0.5 * (old_y_min + old_y_max))
            else:
                cut_coordinate = int(0.5 * (old_x_min + old_x_max))

            new_frame = self.visualisation_panels[current_frame].duplicate()
            while new_frame.name in self.visualisation_panels:
                new_frame.copy_index += 1
                new_frame.name = new_frame.name.replace(
                    f" - {new_frame.copy_index + 1}",
                    f" - {new_frame.copy_index + 2}",
                )

            new_visualisation_panels[new_frame.name] = new_frame
            new_visualisation_panels[new_frame.name].fig_overlay.button_3 = self._make_button_icon()
            new_visualisation_panels[new_frame.name].fig_overlay.button_3.on_click(functools.partial(self.set_to_frame, frame_name=new_frame.name))
            new_visualisation_panels[new_frame.name].bounds_row[0].param.watch(functools.partial(self.set_to_frame, frame_name=new_frame.name), "value")

            new_visualisation_panels[new_frame.name].provide_on_clic_callback(self.on_clic_callback)
            new_visualisation_panels[new_frame.name].provide_on_mouse_move_callback(self.mouse_move_callback)

            if horizontal:
                self.bounds_x[new_frame.name] = (old_x_min, old_x_max)

                self.bounds_y[current_frame] = (old_y_min, cut_coordinate)
                self.bounds_y[new_frame.name] = (cut_coordinate, old_y_max)
            else:
                self.bounds_x[current_frame] = (old_x_min, cut_coordinate)
                self.bounds_x[new_frame.name] = (cut_coordinate, old_x_max)

                self.bounds_y[new_frame.name] = (old_y_min, old_y_max)

            for panel_name in self.visualisation_panels:
                new_visualisation_panels[panel_name] = self.visualisation_panels[
                    panel_name
                ].duplicate(keep_name=True)
                
                new_visualisation_panels[panel_name].fig_overlay.button_3 = self._make_button_icon()
                new_visualisation_panels[panel_name].fig_overlay.button_3.on_click(functools.partial(self.set_to_frame, frame_name=panel_name))
                new_visualisation_panels[panel_name].bounds_row[0].param.watch(functools.partial(self.set_to_frame, frame_name=panel_name), "value")

                new_visualisation_panels[panel_name].provide_on_clic_callback(self.on_clic_callback)
                new_visualisation_panels[panel_name].provide_on_mouse_move_callback(self.mouse_move_callback)

            self.visualisation_panels = new_visualisation_panels

            self.make_grid_stack()

            self.bounds_row.clear()
            self.panel_param_cards.clear()

            self.frame_selector.options = list(self.visualisation_panels.keys())

            for key in self.visualisation_panels:
                self.bounds_row.objects = self.get_bounds_row().objects
                self.panel_param_cards[key] = pn.Card(
                    self.visualisation_panels[key].side_bar,
                    width=350,
                    margin=0,
                    styles=card_style,
                    title=f"{key} parameters",
                )

                self.visualisation_panels[key].bounds_row[0].param.watch(
                    functools.partial(self.set_to_frame, frame_name=key), "value"
                )

            self.change_current_frame(None)
            print("Duplicate over")