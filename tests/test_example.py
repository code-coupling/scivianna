from scivianna.components.overlay_component import Overlay
from scivianna.layout.split import SplitItem, SplitJSHorizontal, SplitJSVertical
from scivianna.panel.line_plot_panel import LineVisualisationPanel
from scivianna.panel.plot_panel import VisualizationPanel
from scivianna_example import demo

def test_demo():
    _, slaves = demo.make_demo(return_slaves = True)

    for slave in slaves:
        slave.terminate()


if __name__ == "__main__":
    test_demo()