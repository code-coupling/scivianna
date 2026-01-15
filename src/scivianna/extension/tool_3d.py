
from pathlib import Path
from typing import TYPE_CHECKING
import panel as pn
import panel_material_ui as pmui
import param

import scivianna.icon
from scivianna.extension.extension import Extension
from scivianna.plotter_3d.plotter_3d import Plotter3D
from scivianna.slave import ComputeSlave

if TYPE_CHECKING:
    from scivianna.panel.visualisation_panel import VisualizationPanel

profile_time = False


with open(Path(scivianna.icon.__file__).parent / "3d_tool.svg", "r") as f:
    icon_svg = f.read()


class SliceTool(Extension):
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
            "Slice tool",
            icon_svg,
            slave,
            plotter,
            panel,
        )
        self.iconsize = "1.0em"

        self.description = """
This extension lets you move around a plane to update 2D plot planes.
"""

        self.display = pmui.Checkbox(
            name="Diplay tool", value=False,
        )
        self.display.param.watch(self.trigger_display, "value")

        self.plotter.on_tool_move(self.on_tool_move)

    def trigger_display(self, *args, **kwargs):
        """Trigger a field change in the visualization panel
        """
        self.plotter.display_tool(self.display.value)

    def make_gui(self,) -> pn.viewable.Viewable:
        """Returns a panel viewable to display in the extension tab.

        Returns
        -------
        pn.viewable.Viewable
            Viewable to display in the extension tab
        """
        return pn.Column(
            self.display,
        )

    def on_tool_move(self, event: param.parameterized.Event):
        location = event.new[12:15]
        x_vector = event.new[:3]
        # y_vector = event.new[4:7]
        z_vector = event.new[8:11]

        print(f"Calling recompute at {location} with axes {x_vector} and {z_vector}")

        self.panel.axes_change_callback(x_vector, z_vector, location)
