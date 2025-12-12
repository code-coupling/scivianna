import pytest
from scivianna.component.overlay_component import Overlay
from scivianna.layout.split import SplitItem, SplitJSHorizontal, SplitJSVertical
from scivianna.panel.panel_1d import LineVisualisationPanel
from scivianna.panel.visualisation_panel import VisualizationPanel
from scivianna_example import demo

@pytest.mark.default
def test_demo():
    _, slaves = demo.make_demo(return_slaves = True)

    for slave in slaves:
        slave.terminate()


if __name__ == "__main__":
    test_demo()