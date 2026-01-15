
from functools import partial
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

        self.xplus = pmui.Button(name="X", button_type="success", width=50)
        self.xplus.on_click(partial(self.move_matrix_to_axis, axis_name="X"))

        self.yplus = pmui.Button(name="Y", button_type="success", width=50)
        self.yplus.on_click(partial(self.move_matrix_to_axis, axis_name="Y"))

        self.zplus = pmui.Button(name="Z", button_type="success", width=50)
        self.zplus.on_click(partial(self.move_matrix_to_axis, axis_name="Z"))

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
            pn.Row(self.xplus, self.yplus, self.zplus)
        )

    def on_tool_move(self, event: param.parameterized.Event):
        print(event.new)

        location = event.new[12:15]
        x_vector = event.new[:3]
        # y_vector = event.new[4:7]
        z_vector = event.new[8:11]

        print(f"Calling recompute at {location} with axes {x_vector} and {z_vector}")

        self.panel.axes_change_callback(x_vector, z_vector, location)

    def move_matrix_to_axis(self, event, axis_name: str):
        location = self.plotter.get_tool_matrix()[12:]

        if location == []:
            location = [0, 0, 0, 1]

        if axis_name == "X":
            new_matrix = [
                0, 1, 0, 0,
                1, 0, 0, 0,
                0, 0, 1, 0,
            ] + location
        elif axis_name == "Y":
            new_matrix = [
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
            ] + location
        elif axis_name == "Z":
            new_matrix = [
                0, 1, 0, 0,
                0, 0, 1, 0,
                1, 0, 0, 0,
            ] + location
        else:
            raise ValueError(f"Axis {axis_name} unknown, use X Y or Z.")

        self.plotter.set_tool_matrix(new_matrix)
