from typing import TYPE_CHECKING
import panel as pn
import panel_material_ui as pmui
from scivianna.extension.axes import icon_svg
from scivianna.extension.extension import Extension
from scivianna.plotter_3d.plotter_3d import Plotter3D
from scivianna.slave import ComputeSlave

if TYPE_CHECKING:
    from scivianna.panel.visualisation_panel import VisualizationPanel


class Axes(Extension):
    """Extension to load files and send them to the slave."""

    plotter: Plotter3D

    def __init__(
        self, slave: ComputeSlave, plotter: Plotter3D, panel: "VisualizationPanel"
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
        assert isinstance(
            plotter, Plotter3D
        ), "Axes extension is built for a Plotter3D only"
        super().__init__(
            "Axes customization",
            icon_svg,
            slave,
            plotter,
            panel,
        )

        self.description = """
The axes extension allows you to edit the axes vectors or the plot bounds along both axes if applicable.

You can also hide/show the axes on the plot and force a plot update.
"""

        self.iconsize = "1.0em"

        self.hide_show_button = pmui.Checkbox(
            label="Toggle axes",
            description="Display plot axis",
            value=True, width=280
        )
        self.hide_show_button.param.watch(self.toggle_axis_visibility, "value")

        self.font_size_input = pmui.FloatInput(
            label="Font size",
            description="Axes label font size", value=1, start=0, end=100, width=280
        )
        self.font_size_input.param.watch(self.change_font_size, "value")

        self.label_distance_input = pmui.FloatInput(
            label="Label distance",
            description="Axes label distance", value=1, start=0, end=100, width=280
        )
        self.label_distance_input.param.watch(self.change_label_distance, "value")

    @pn.io.hold()
    def change_label_distance(self, *args, **kwargs):
        """Hides and shows the figure axis

        Parameters
        ----------
        _ : Any
            Button clic event
        """
        self.plotter.set_axes_label_distance(self.label_distance_input.value)

    def change_font_size(self, *args, **kwargs):
        """Hides and shows the figure axis

        Parameters
        ----------
        _ : Any
            Button clic event
        """
        self.plotter.set_axes_font_size(self.font_size_input.value)

    def toggle_axis_visibility(self, *args, **kwargs):
        """Hides and shows the figure axis

        Parameters
        ----------
        _ : Any
            Button clic event
        """
        self.font_size_input.visible = self.hide_show_button.value
        self.label_distance_input.visible = self.hide_show_button.value
        self.plotter.display_axes(self.hide_show_button.value)

    def make_gui(
        self,
    ) -> pn.viewable.Viewable:
        """Returns a panel viewable to display in the extension tab.

        Returns
        -------
        pn.viewable.Viewable
            Viewable to display in the extension tab
        """
        return pmui.Column(
            pmui.Typography("Hide/show axis"),
            self.hide_show_button,
            self.font_size_input,
            self.label_distance_input,
            margin=0,
        )
