from scivianna.constants import X, Y, Z
from scivianna.enums import UpdateEvent
from scivianna.layout.split import (
    SplitItem,
    SplitDirection,
    SplitLayout,
)
from scivianna.notebook_tools import get_med_panel, _serve_panel

def get_panel(_, return_slaves = False) -> SplitLayout:

    med_1 = get_med_panel(geo=None, title="MEDCoupling visualizer XY")

    med_1.set_field("INTEGRATED_POWER")
    med_1.update_event = UpdateEvent.CLIC

    if return_slaves:
        return SplitLayout(med_1), [med_1.get_slave()]
    else:   
        return SplitLayout(med_1)

if __name__ == "__main__":
    _serve_panel(get_panel_function=get_panel)