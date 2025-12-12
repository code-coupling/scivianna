import panel as pn
from panel.reactive import ReactiveHTML
from panel.custom import Child, ReactiveHTML
import param


class Overlay(ReactiveHTML):
    """This component allow displaying buttons over a figure only when the mouse is in the area."""

    figure = Child()
    """Figure : main component"""
    button_1 = Child()
    """First button (displayed on the top right of the figure)"""
    button_2 = Child()
    """Second button (displayed below the button_1)"""
    button_3 = Child()
    """Third button (displayed below the button_2)"""
    title = Child()
    """Figure title (displayed on the top left of the figure)"""
    message = Child()
    """Figure message (displayed on the bottom left of the figure)"""

    distance_from_right: param.String = param.String("10px")
    """Distance between the button and the right of the figure (increased when the axis are displayed)"""
    distance_from_left: param.String = param.String("10px")
    """Distance between the title and the left of the figure (increased when the axis are displayed)"""

    mouse_in: param.Boolean = param.Boolean(False)

    _template = """
                    <div id="figure-container" style="position: relative; width: 100%; height: 100%;"
                        onmouseenter="${_mouse_entered}" 
                        onmouseleave="${_hide_buttons}">
                        <div id="figure" style="width: 100%; height: 100%;">
                            ${figure}
                        </div>
                        <div id="button-container_1" style="position: absolute; top: 10px; right: ${distance_from_right};">
                            ${button_1}
                        </div>
                        <div id="button-container_2" style="position: absolute; top: 60px; right: ${distance_from_right};">
                            ${button_2}
                        </div>
                        <div id="button-container_3" style="position: absolute; top: 100px; right: ${distance_from_right};">
                            ${button_3}
                        </div>
                        <div id="title-container" style="position: absolute; top: 10px; left: ${distance_from_left};">
                            ${title}
                        </div>
                        <div id="message-container" style="position: absolute; bottom: 10px; left: ${distance_from_left};">
                            ${message}
                        </div>
                    </div>
                """
    """HTML code of the elemet display"""

    @pn.io.hold()
    def _hide_buttons(self, event):
        """Hide all element on top of the figure

        Parameters
        ----------
        event : Any
            Argument to make the function linkable
        """
        self.mouse_in = False
        if self.button_1 is not None:
            self.button_1.visible = False
        if self.button_2 is not None:
            self.button_2.visible = False
        if self.button_3 is not None:
            self.button_3.visible = False
        if self.title is not None:
            self.title.visible = False

    def _mouse_entered(self, event):
        """Runs a timeout event asking to display the buttons if the mouse is still in the frame after a given time. The time out prevents flikering the app when crossing through several panels.

        Parameters
        ----------
        event : Any
            Argument to make the function linkable
        """
        self.mouse_in = True

        if pn.state.curdoc is not None:
            pn.state.curdoc.add_timeout_callback(self._show_buttons, 300)

    def show_temporary_message(self, text: str, timeout: int):
        """Runs a timeout event asking to display the buttons if the mouse is still in the frame after a given time. The time out prevents flikering the app when crossing through several panels.

        Parameters
        ----------
        text : str
            Message to display
        timeout : int
            Time after which the message disappears in ms
        """
        if self.message is not None:
            self.message.object = text

            self.message.visible = True

            if pn.state.curdoc is not None:
                pn.state.curdoc.add_timeout_callback(self._hide_message, timeout)

    @pn.io.hold()
    async def _show_buttons(
        self,
    ):
        """Show all element on top of the figure if the mouse is in the frame"""
        if self.mouse_in:
            if self.button_1 is not None:
                self.button_1.visible = True
            if self.button_2 is not None:
                self.button_2.visible = True
            if self.button_3 is not None:
                self.button_3.visible = True
            if self.title is not None:
                self.title.visible = True

    async def _hide_message(
        self,
    ):
        if self.message is not None:
            self.message.visible = False


if __name__ == "__main__":
    from bokeh.plotting import figure

    fig = figure(
        width_policy="max",
        height_policy="max",
        toolbar_location=None,
    )

    fig.line([0, 1, 2, 3, 4], [0, 2, 4, 2, 1])
    fig.xaxis.visible = False
    fig.yaxis.visible = False

    bokeh_pane = pn.pane.Bokeh(
        fig,
        margin=0,
        styles={"border": "2px solid lightgray"},
        width_policy="max",
        height_policy="max",
    )

    def trigger_function(_):
        print(_)

    button_1 = pn.widgets.Button(
        name="Button_1",
        margin=0,
    )
    button_2 = pn.widgets.ButtonIcon(
        # margin=0,
        size="2.5em",
        icon="adjustments",
    )

    button_1.on_click(trigger_function)

    overlay = Overlay(
        figure=bokeh_pane,
        button_1=button_1,
        button_2=button_2,
        styles={"border": "2px solid lightgray"},
        margin=0,
        width_policy="max",
        height_policy="max",
    )

    def hide_show_axis(_):
        if fig.toolbar_location is None:
            fig.toolbar_location = "right"
            fig.xaxis.visible = True
            fig.yaxis.visible = True
            overlay.distance_from_right = "40px"
            overlay.distance_from_left = "40px"
        else:
            fig.toolbar_location = None
            fig.xaxis.visible = False
            fig.yaxis.visible = False
            overlay.distance_from_right = "10px"
            overlay.distance_from_left = "10px"

    button_2.on_click(hide_show_axis)

    pn.Column(
        # bokeh_pane,
        overlay,
        width_policy="max",
        height_policy="max",
        margin=0,
    ).show()
