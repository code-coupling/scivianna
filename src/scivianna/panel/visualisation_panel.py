from typing import Callable, List, Tuple, Type, Union
import numpy as np
import panel as pn
import panel_material_ui as pmui
import os

from scivianna.data.data_container import DataContainer
from scivianna.extension.extension import Extension

from scivianna.interface.generic_interface import Geometry2D

from scivianna.enums import GeometryType, UpdateEvent
from scivianna.slave import ComputeSlave

from scivianna.panel.gui import GUI
from scivianna.plotter_2d.generic_plotter import Plotter2D

pn.config.inline = True

class VisualizationPanel:
    """Visualisation panel associated to a code."""

    name: str
    """ Panel name
    """
    slave: ComputeSlave
    """ Slave to which request the plots
    """
    plotter: Plotter2D
    """ 2D plotter displaying and updating the graph : TODO generic plotter
    """
    main_frame: pmui.Container
    """ Main frame displaying the geometry.
    """
    extensions: List[Extension]
    """ List of extensions attached to the panel
    """

    current_data: DataContainer
    """ Displayed data and their properties.
    """
    update_event: Union[UpdateEvent, List[UpdateEvent]] = UpdateEvent.RECOMPUTE
    """ On what event does the panel recompute itself
    """
    sync_field: bool = False
    """ On what event does the panel recompute itself
    """

    def __init__(
            self, 
            slave: ComputeSlave, 
            name="", 
            extensions: List[Extension] = []
        ):
        """Visualization panel constructor

        Parameters
        ----------
        slave : ComputeSlave
            ComputeSlave object to which request the plots.
        name : str
            Name of the panel.
        extensions : List[Extension]
            List of extensions loaded with the visualizer.
        """
        #         
        #   Initializing attributes
        #         
        self.name = name
        self.copy_index = 0
        self.slave = slave
        self.update_polygons = False
        """Need to update the data at the next async call"""
        self.field_change_callback: Callable = None
        """Function to call when the field is changed"""

        self.__data_to_update: bool = False
        self.__new_data = {}
        """New data to set in the colorbar and in the columndatasources"""

        # 
        #   Saving code interface properties
        #         
        code_interface: Type[Geometry2D] = self.slave.code_interface
        
        # 
        #   Extensions creation
        #         
        for extension in code_interface.extensions:
            if not issubclass(extension, Extension):
                raise TypeError(f"Extension {extension} declared in {code_interface.extensions} extensions is not a subclass of {Extension}")
            extensions.append(extension)

        self.extensions = [
            e(
                self.slave,
                self.plotter,
                self
            )
            for e in extensions
        ]

        # 
        #   Building layout
        #         
        self.gui = GUI(
            self.extensions
        )
        self.gui_panel = self.gui.make_panel()

        self.figure = pn.Column(self.plotter.make_panel(), sizing_mode="stretch_both")
        pn.io.push_notebook(self.figure)

        self.main_frame = pn.Row(
            self.gui_panel,
            self.figure,
            margin=0,
            sizing_mode="stretch_both",
        )

        self.periodic_recompute_added = False
        """Coupling periodic update"""
        self.marked_to_recompute = False
        """Recompute requested by a coordinates/field change on API side"""

        for extension in self.extensions:
            self.plotter.provide_on_clic_callback(extension.on_mouse_clic)
            self.plotter.provide_on_mouse_move_callback(extension.on_mouse_move)

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

        return new_visualiser

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


    # 
    # #
    # #     API to provide in the panels
    # #
    # 

    @pn.io.hold()
    def async_update_data(
        self,
    ):
        """Update the figures and buttons based on what was added in self.__new_data. This function is called between two servers ticks to prevent multi-users collisions."""
        raise NotImplementedError()

    def recompute(
        self, *args, **kwargs
    ):
        """Recomputes the figure based on the new bounds and parameters.
        """
        raise NotImplementedError()

    def provide_on_mouse_move_callback(self, callback: Callable):
        """Stores a function to call everytime the user moves the mouse on the plot.
        Functions arguments are location, cell_id.

        Parameters
        ----------
        callback : Callable
            Function to call.
        """
        self.plotter.provide_on_mouse_move_callback(callback)

    def provide_on_clic_callback(self, callback: Callable):
        """Stores a function to call everytime the user clics on the plot.
        Functions arguments are location, cell_id.

        Parameters
        ----------
        callback : Callable
            Function to call.
        """
        self.plotter.provide_on_clic_callback(callback)

    def provide_field_change_callback(self, callback: Callable):
        """Stores a function to call everytime the displayed field is changed.
        the functions takes a string as argument.

        Parameters
        ----------
        callback : Callable
            Function to call.
        """
        self.field_change_callback = callback

    def recompute_at(self, position: Tuple[float, float, float], cell_id: str):
        """Triggers a panel recomputation at the provided location. Called by layout update event.

        Parameters
        ----------
        position : Tuple[float, float, float]
            Location to provide to the slave
        cell_id : str
            cell id to provide to the slave
        """
        raise NotImplementedError()

    def set_field(self, field_name: str):
        """Updates the plotted field

        Parameters
        ----------
        field_name : str
            New field to display
        """
        raise NotImplementedError()

    def set_colormap(self, colormap: str):
        """Sets the current color map

        Parameters
        ----------
        colormap : str
            Color map name
        """
        raise NotImplementedError()
