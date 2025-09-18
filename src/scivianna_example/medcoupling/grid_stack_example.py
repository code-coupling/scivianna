from typing import Dict
from scivianna.layout.gridstack import GridStackLayout
from scivianna.panel.plot_panel import VisualizationPanel
from scivianna.notebook_tools import (
    get_med_panel
)

import panel as pn


def get_panel():
    visualisation_panels: Dict[str, VisualizationPanel] = {}

    visualisation_panels["MEDCoupling visualizer 1"] = get_med_panel(
        geo=None, title="MEDCoupling visualizer 1"
    )
    visualisation_panels["MEDCoupling visualizer 2"] = get_med_panel(
        geo=None, title="MEDCoupling visualizer 2"
    )
    try:
        visualisation_panels["MEDCoupling visualizer 3"] = get_med_panel(
            geo=None, title="MEDCoupling visualizer 3"
        )

        bounds_x = {
            "MEDCoupling visualizer 1": (0, 5),
            "MEDCoupling visualizer 2": (0, 5),
            "MEDCoupling visualizer 3": (5, 10),
        }

        bounds_y = {
            "MEDCoupling visualizer 1": (0, 5),
            "MEDCoupling visualizer 2": (5, 10),
            "MEDCoupling visualizer 3": (0, 10),
        }
    except ImportError:
        bounds_x = {
            "MEDCoupling visualizer 1": (0, 10),
            "MEDCoupling visualizer 2": (0, 10),
        }

        bounds_y = {
            "MEDCoupling visualizer 1": (0, 5),
            "MEDCoupling visualizer 2": (5, 10),
        }

    return GridStackLayout(visualisation_panels, bounds_y, bounds_x)


def get_template():
    panel = get_panel()
    return pn.template.BootstrapTemplate(
        main=[
            pn.Column(
                panel.bounds_row,
                panel.main_frame,
                height_policy="max",
                width_policy="max",
                margin=0,
            )
        ],
        sidebar=[panel.side_bar],
        title="Gridstack demo",
    )


if __name__ == "__main__":
    #   Serving panel as main, file executed with a command : "python my_file.py"
    import socket

    ip_adress = socket.gethostbyname(socket.gethostname())

    """
        Catching a free port to provide to pn.serve
    """
    sock = socket.socket()
    sock.bind((ip_adress, 0))
    port = sock.getsockname()[1]
    sock.close()

    server = pn.serve(
        get_template,
        address=ip_adress,
        websocket_origin=f"{ip_adress}:{port}",
        port=port,
        threaded=True,
    )
else:
    panel = get_panel()
    #   Providing servable panel, file executed with a command : "python -m panel serve my_file.py"
    panel.side_bar.servable(target="sidebar")

    pn.Column(
        panel.bounds_row,
        panel.main_frame,
        height_policy="max",
        width_policy="max",
        margin=0,
    ).servable(target="main")
