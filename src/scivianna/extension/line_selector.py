
from typing import TYPE_CHECKING
import panel as pn
import panel_material_ui as pmui

from scivianna.extension.extension import Extension
from scivianna.plotter_1d.generic_plotter import Plotter1D
from scivianna.slave import ComputeSlave

if TYPE_CHECKING:
    from scivianna.panel.visualisation_panel import VisualizationPanel

profile_time = False


class LineSelector(Extension):
    """ Extension used to select the displayed line in a Panel1D.
    """

    def __init__(
        self,
        slave: ComputeSlave,
        plotter: Plotter1D,
        panel: "VisualizationPanel"
    ):
        """Constructor of the extension, saves the slave and the panel

        Parameters
        ----------
        slave : ComputeSlave
            Slave computing the displayed data
        plotter : Plotter1D
            Figure plotter
        panel : VisualizationPanel
            Panel to which the extension is attached
        """
        assert isinstance(plotter, Plotter1D), "LineSelector extension is only compatible with Plotter1D"
        super().__init__(
            "Line selection",
            "line_axis",
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
            name="Displayed plot",
            options=fields_list,
            value=fields_list[0],
            width = 280
        )

        self.field_color_selector.param.watch(self.trigger_field_change, "value")

    def trigger_field_change(self, *args, **kwargs):
        """Trigger a field change in the visualization panel
        """
        self.panel.set_field(self.field_color_selector.value)

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
            set(
                self.field_color_selector.options + self.slave.get_labels()
            )
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
        )
    