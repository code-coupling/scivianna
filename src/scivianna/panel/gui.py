from functools import partial
from pathlib import Path
from typing import List, Tuple

import panel_material_ui as pmui
import panel as pn

from scivianna.extension.extension import Extension


class GUI:
    def __init__(
        self, 
        extensions: List[Extension]
    ):
        s = "6em"
        button_margin_x = 4
        button_margin_y = 10
        button_margin = (button_margin_x, button_margin_y)

        self.extensions = extensions

        self.buttons = []

        self.open_button = pmui.IconButton(
            icon="keyboard_double_arrow_right",
            size=s,
            description="Open extensions",
            margin=button_margin,
        )

        self.close_button = pmui.IconButton(
            icon="keyboard_double_arrow_left",
            size=s,
            description="Close extensions",
            margin=button_margin,
            visible=False,
        )

        self.options_widget = pmui.Column(
            self.open_button, self.close_button
        )

        self.drawer_column = pmui.Column(
            margin=0
        )

        self.drawer = pmui.Drawer(self.drawer_column, size=300, variant="persistent")

        self.open_button.on_click(self.open_close_drawer)
        self.close_button.on_click(self.open_close_drawer)

        for extension in extensions:
            self.register_new_extension(
                pmui.IconButton(
                    icon=extension.icon,
                    size=extension.iconsize,
                    description=extension.title,
                    margin=button_margin,
                ),
                pn.Column(
                    pmui.Typography(
                        "## "+extension.title,
                        width_policy="max",
                    ),
                    pmui.Typography(
                        extension.description,
                        width_policy="max",
                    ),
                    extension.make_gui(),
                )
            )

        self.active_extension = self.buttons[0]

        self.change_drawer(None, self.active_extension)

    @pn.io.hold()
    def update_colors(
        self,
    ):
        for b in self.buttons:
            b[0].color = "primary"
            b[1].visible = False
            if b == self.active_extension and self.drawer.open:
                b[0].color = "secondary"
                b[1].visible = True

    @pn.io.hold()
    def change_drawer(self, _, extension: pmui.IconButton):
        self.drawer.open = True
        self.open_button.visible = False
        self.close_button.visible = True

        self.active_extension = extension

        self.update_colors()

    @pn.io.hold()
    def open_close_drawer(self, _):
        self.drawer.open = not self.drawer.open
        self.open_button.visible = not self.open_button.visible
        self.close_button.visible = not self.close_button.visible

        self.update_colors()

    def make_panel(
        self,
    ):
        return pn.Row(
            self.drawer,
            self.options_widget,
            pmui.Divider(
                orientation="vertical",
                styles={"background": "#9F9F9F"},
                variant="fullWidth",
                sizing_mode="stretch_height",
                margin=0,
            ),
            margin=0,
        )

    def register_new_extension(self, button: pmui.IconButton, col: pn.Column):
        ext = (button, col)

        self.buttons.append(ext)
        col.visible = False
        self.options_widget.append(button)
        
        # Adding col first to keep the selection at the bottom
        self.drawer_column.insert(0, col)
        
        button.on_click(partial(self.change_drawer, extension=ext))


if __name__ == "__main__":
    import socket

    ip_adress = socket.gethostbyname(socket.gethostname())

    """
        Catching a free port to provide to pn.serve
    """
    sock = socket.socket()
    sock.bind((ip_adress, 0))
    port = sock.getsockname()[1]
    sock.close()

    def get_panel():
        gui = GUI()
        return gui.make_panel()

    pn.serve(
        get_panel,
        address=ip_adress,
        websocket_origin=f"{ip_adress}:{port}",
        port=port,
        threaded=True,
    )
