from pathlib import Path
import numpy as np

import scivianna
from scivianna.constants import GEOMETRY
from scivianna.component.r3f_component.app import ReactThreeFiber, get_rd_bu
from scivianna.extension.field_selector import set_colors_list
from scivianna.interface.med_interface import MEDInterface


med = MEDInterface()

med.read_file(
    str(Path(scivianna.__file__).parent / "input_file" / "power.med"), GEOMETRY
)

data, _ = med.compute_3D_data(
    0., 1., 0., 1., 0., 1., None, {}
)
data.cell_values = list(med.get_value_dict("INTEGRATED_POWER", data.cell_ids, {}).values())
set_colors_list(
    data,
    med,
    "INTEGRATED_POWER",
    "viridis",
    False,
    {},
)

r3f = ReactThreeFiber(
    sizing_mode="stretch_both",
    display_color_map=True,
    color_map_colors=get_rd_bu(np.linspace(0, 1, 11), html=True),
    slice_tool_visible=True
)

r3f.plot_data3d(data)

r3f.show()
