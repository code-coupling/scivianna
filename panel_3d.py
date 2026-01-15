from pathlib import Path

import scivianna
from scivianna.constants import GEOMETRY
from scivianna.interface.med_interface import MEDInterface
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

    return panel


if __name__ == "__main__":
    _serve_panel(get_panel_function=get_3d_med_panel)
