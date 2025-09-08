from pathlib import Path
import matplotlib.pyplot as plt

import scivianna
from scivianna.constants import GEOMETRY, MATERIAL, X, Y
from scivianna.slave import ComputeSlave
from scivianna.plotter_2d.api import plot_frame_in_axes

from scivianna.interface.med_interface import MEDInterface


def test_plot_api():
    """Simple test to make sure things happen before more tests are actually implemented
    """

    # Field example
    slave = ComputeSlave(MEDInterface)
    slave.read_file(
        Path(scivianna.__file__).parent / "default_jdd" / "power.med",
        GEOMETRY,
    )

    fig, axes = plt.subplots(1, 1, figsize=(8, 7))

    plot_frame_in_axes(
        slave,
        u=X,
        v=Y,
        u_min=-10.0,
        u_max=10.0,
        v_min=-10.0,
        v_max=10.0,
        u_steps=0,
        v_steps=0,
        w_value=0.0,
        coloring_label="INTEGRATED_POWER",
        color_map="viridis",
        display_colorbar=True,
        axes=axes,
    )

    slave.terminate()
