from typing import Dict
from scivianna.constants import X, Y, Z
from scivianna.enums import UpdateEvent
from scivianna.layout.gridstack import GridStackLayout
from scivianna.notebook_tools import get_med_panel, _make_template
from scivianna.panel.plot_panel import VisualizationPanel


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

    # Terminating so the tests doesn't hold after finishing
    for panel in visualisation_panels.values():
        panel.get_slave().terminate()

    return GridStackLayout(visualisation_panels, bounds_y, bounds_x)

def get_template():
    panel = get_panel()
    return _make_template(panel)


def test_import_gridstack():
    """Test importing the gridstack layout and make the panel without opening it
    """
    get_template()
    return True