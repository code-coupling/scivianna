from pathlib import Path

import scivianna
from scivianna.constants import GEOMETRY
from scivianna.enums import UpdateEvent
from scivianna.interface.med_interface import MEDInterface
from scivianna.layout.split import SplitDirection, SplitItem, SplitLayout
from scivianna.panel.panel_2d import Panel2D
from scivianna.panel.panel_3d import Panel3D
from scivianna.slave import ComputeSlave
from scivianna.notebook_tools import _serve_panel


def get_3d_med_panel(*args, **kwargs):
    med = ComputeSlave(MEDInterface)
    med.read_file(
        str(Path(scivianna.__file__).parent / "input_file" / "power.med"), GEOMETRY
    )

    panel = Panel3D(med, name="3D plot")
    panel.set_field("INTEGRATED_POWER")

    med2 = ComputeSlave(MEDInterface)
    med2.read_file(
        str(Path(scivianna.__file__).parent / "input_file" / "power.med"), GEOMETRY
    )

    panel2 = Panel2D(med2, name="2D plot")
    panel2.set_field("INTEGRATED_POWER")
    panel2.update_event = UpdateEvent.AXES_CHANGE

    layout = SplitLayout(SplitItem(panel, panel2, SplitDirection.VERTICAL))

    return layout


if __name__ == "__main__":
    _serve_panel(get_panel_function=get_3d_med_panel)
