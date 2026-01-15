
from typing import TYPE_CHECKING
import panel as pn
import panel_material_ui as pmui

import numpy as np
from scivianna.data.data3d import Data3D
from scivianna.enums import VisualizationMode
from scivianna.extension.extension import Extension
from scivianna.extension.field_selector import set_colors_list
from scivianna.plotter_3d.plotter_3d import Plotter3D
from scivianna.slave import ComputeSlave
from scivianna.utils.color_tools import beautiful_color_maps

if TYPE_CHECKING:
    from scivianna.panel.visualisation_panel import VisualizationPanel

profile_time = False


class FieldSelector(Extension):
    """ Extension used to select the displayed field and edit its colors.
    """
    plotter: Plotter3D

    def __init__(
        self,
        slave: ComputeSlave,
        plotter: Plotter3D,
        panel: "VisualizationPanel"
    ):
        """Constructor of the extension, saves the slave and the panel

        Parameters
        ----------
        slave : ComputeSlave
            Slave computing the displayed data
        plotter : Plotter3D
            Figure plotter
        panel : VisualizationPanel
            Panel to which the extension is attached
        """
        super().__init__(
            "Color map",
            "palette",
            slave,
            plotter,
            panel,
        )

        self.description = """
The color map extension lets you decide which field is being displayed on the cells, and what colorbar is used.

If a color bar is used, you can decide to center it on zero.
"""

        fields_list = self.slave.get_labels()
        self.field_color_selector = pmui.Select(
            name="Color field",
            options=fields_list,
            value=fields_list[0],
            width=280
        )

        self.field_color_selector.param.watch(self.trigger_field_change, "value")
        self.panel.param.watch(self.receive_colormap_change, "colormap")

        self.color_map_selector = pn.widgets.ColorMap(
            options=beautiful_color_maps,
            swatch_width=60,
            width_policy='max'
        )

        self.color_map_selector.width = self.color_map_selector.height
        self.center_colormap_on_zero_tick = pmui.Checkbox(
            name="Center color map on zero", value=False,
            visible=slave.get_label_coloring_mode(self.field_color_selector.value) == VisualizationMode.FROM_VALUE,
        )

        self.color_map_selector.value_name = "BuRd"
        self.color_map_selector.value = beautiful_color_maps["BuRd"]

        self.color_map_selector.param.watch(self.trigger_colormap_change, "value")
        self.center_colormap_on_zero_tick.param.watch(self.trigger_update, "value")

        self.opacity_input = pmui.FloatInput(label='Cells opacity', value=1., start=0, end=1, width=280)
        self.opacity_input.param.watch(self.on_opacity_change, "value")

        self.light_input = pmui.FloatInput(label='Color light', value=1., start=0, end=100, width=280)
        self.light_input.param.watch(self.on_light_change, "value")

        self.edge_visible = pmui.Checkbox(
            name="Edges visible", value=True,
            visible=slave.get_label_coloring_mode(self.field_color_selector.value) == VisualizationMode.FROM_VALUE,
            width=280
        )

        self.edge_visible.param.watch(self.on_edge_visible_change, "value")

    def trigger_field_change(self, *args, **kwargs):
        """Trigger a field change in the visualization panel
        """
        self.center_colormap_on_zero_tick.visible = self.slave.get_label_coloring_mode(self.field_color_selector.value) == VisualizationMode.FROM_VALUE
        self.panel.set_field(self.field_color_selector.value)

    def receive_colormap_change(self, *args, **kwargs):
        """Receive a field change from the visualization panel
        """
        if self.panel.colormap != self.color_map_selector.value_name:
            self.color_map_selector.value_name = self.panel.colormap

    def trigger_colormap_change(self, *args, **kwargs):
        """Trigger a field change in the visualization panel
        """
        self.panel.set_colormap(self.color_map_selector.value_name)
        self.panel.recompute()

    def trigger_update(self, *args, **kwargs):
        """Trigger a color map change in the visualization panel
        """
        self.panel.recompute()

    @pn.io.hold()
    def on_file_load(self, file_path: str, file_key: str):
        """Function called when the user requests a change of field on the GUI

        Parameters
        ----------
        file_path : str
            Path of the loaded file
        file_key : str
            Key associated to the loaded file
        """
        self.field_color_selector.options = list(
            self.slave.get_labels()
        )
        self.field_color_selector.value = self.field_color_selector.options[0]

    def on_updated_data(self, data: Data3D):
        """Function called when the displayed data is being updated. Extension can edit the data on its way to the plotter.

        Parameters
        ----------
        data : Data3D
            Data to display
        """
        set_colors_list(
            data,
            self.slave,
            self.field_color_selector.value,
            self.color_map_selector.value_name,
            self.center_colormap_on_zero_tick.value,
            {},
        )

    def make_gui(self,) -> pn.viewable.Viewable:
        """Returns a panel viewable to display in the extension tab.

        Returns
        -------
        pn.viewable.Viewable
            Viewable to display in the extension tab
        """
        return pn.Column(
            self.field_color_selector,
            self.color_map_selector,
            self.center_colormap_on_zero_tick,
            self.edge_visible,
            self.opacity_input,
            self.light_input,
        )

    def on_field_change(self, field_name: str):
        """Function called when the user requests a displayed field change

        Parameters
        ----------
        field_name : str
            Name of the new displayed field
        """
        self.field_color_selector.value = field_name

    def on_light_change(self, event):
        """Function called when the user requests a displayed field change

        Parameters
        ----------
        event
            Function triggering event
        """
        self.plotter.set_light_intensity(self.light_input.value)

    def on_opacity_change(self, event):
        """Function called when the user requests a displayed field change

        Parameters
        ----------
        event
            Function triggering event
        """
        self.plotter.set_opacity(self.opacity_input.value)

    def on_edge_visible_change(self, event):
        """Function called when the user requests a displayed field change

        Parameters
        ----------
        event
            Function triggering event
        """
        self.plotter.set_visible_edges(self.edge_visible.value)

