
from scivianna.enums import UpdateEvent
from scivianna.layout.split import SplitLayout
from scivianna.panel.visualisation_panel import (
    VisualizationPanel
)
from scivianna.notebook_tools import get_med_panel, _serve_panel

def get_panel(*args, return_slaves = False, **kwargs) -> VisualizationPanel:

    med_1 = get_med_panel(geo=None, title="MEDCoupling visualizer XY")

    med_1.set_field("INTEGRATED_POWER")
    med_1.update_event = UpdateEvent.CLIC

    if return_slaves:
        return SplitLayout(med_1), [med_1.get_slave()]
    else:   
        return SplitLayout(med_1)
    
if __name__ == "__main__":
    # get_panel().show()
    _serve_panel(get_panel_function=get_panel)