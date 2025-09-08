from scivianna.constants import X, Y, Z
from scivianna.enums import UpdateEvent
from scivianna.layout.split import (
    SplitItem,
    SplitDirection,
    SplitLayout,
)
from scivianna.notebook_tools import get_med_panel, _make_template



def get_panel(_) -> SplitLayout:

    med_1 = get_med_panel(geo=None, title="MEDCoupling visualizer XY")
    med_2 = get_med_panel(geo=None, title="MEDCoupling visualizer XZ")
    med_3 = get_med_panel(geo=None, title="MEDCoupling visualizer YZ")

    med_1.update_event = UpdateEvent.CLIC

    med_2.update_event = UpdateEvent.CLIC
    med_2.set_coordinates(u=X, v=Z)

    med_3.update_event = UpdateEvent.CLIC
    med_3.set_coordinates(u=Y, v=Z)

    med_1.set_field("INTEGRATED_POWER")
    med_2.set_field("INTEGRATED_POWER")
    med_3.set_field("INTEGRATED_POWER")

    split = SplitItem(med_1, med_2, SplitDirection.VERTICAL)
    split = SplitItem(split, med_3, SplitDirection.HORIZONTAL)

    return SplitLayout(split)


def get_template():
    panel:SplitLayout = get_panel()
    return _make_template(
        panel,
        title="Split item demo",
    )

def test_import_split():
    """Test importing the split layout and make the panel without opening it
    """
    get_template()