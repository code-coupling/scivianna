import functools
from typing import Dict, TYPE_CHECKING
import panel as pn
from scivianna.component.server_file_browser import ServerFileBrowser
from scivianna.constants import GEOMETRY
from scivianna.extension.extension import Extension
from scivianna.plotter_2d.generic_plotter import Plotter2D
from scivianna.slave import ComputeSlave

if TYPE_CHECKING:
    from scivianna.panel.visualisation_panel import VisualizationPanel


class FileLoader(Extension):
    """Extension to load files and send them to the slave."""

    def __init__(
        self,
        slave: ComputeSlave,
        plotter: Plotter2D,
        panel: "VisualizationPanel"
    ):
        """Constructor of the extension, saves the slave and the panel

        Parameters
        ----------
        slave : ComputeSlave
            Slave computing the displayed data
        plotter : Plotter2D
            Figure plotter
        panel : VisualizationPanel
            Panel to which the extension is attached
        """
        super().__init__(
            "Load new files",
            "file_open",
            slave,
            plotter,
            panel,
        )

        self.description = """
The file loader extension lets you browse files on the server file system to provide it to the code interface.
"""
        """
            Widget To send the input file
        """

        self.file_browsers: Dict[str, ServerFileBrowser] = {}

        def load_file(event, browser_name: str):
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

                self.slave.read_file(file_path, browser_name)

                self.panel.recompute()

        file_input_list = self.slave.get_file_input_list()

        for name, _ in file_input_list:
            self.file_browsers[name] = ServerFileBrowser(
                name=str(name),
                width=280
            )
            self.file_browsers[name].param.watch(
                functools.partial(load_file, browser_name=name), "selected_file"
            )

        self.file_loader_list = []
        for fi in self.file_browsers:
            self.file_loader_list.append(
                pn.pane.Markdown(f"{fi} file browser", margin=(0, 0, 0, 0))
            )
            self.file_loader_list.append(self.file_browsers[fi])

    def make_gui(
        self,
    ) -> pn.viewable.Viewable:
        """Returns a panel viewable to display in the extension tab.

        Returns
        -------
        pn.viewable.Viewable
            Viewable to display in the extension tab
        """
        return pn.Column(
                *self.file_loader_list,
                margin=(0, 0, 10, 10),
            )
