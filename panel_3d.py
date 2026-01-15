from pathlib import Path

import scivianna
from scivianna.constants import GEOMETRY
from scivianna.interface.med_interface import MEDInterface
from scivianna.panel.panel_3d import Panel3D
from scivianna.slave import ComputeSlave

if __name__ == "__main__":
    med = ComputeSlave(MEDInterface)
    med.read_file(
        str(Path(scivianna.__file__).parent / "input_file" / "power.med"), GEOMETRY
    )

    panel = Panel3D(med, name="3D plot")
    panel.show()
