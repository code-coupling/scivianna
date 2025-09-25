from pathlib import Path
import matplotlib.pyplot as plt

import scivianna
from scivianna.constants import GEOMETRY, MATERIAL, X, Y
from scivianna.slave import ComputeSlave
from scivianna.plotter_2d.api import plot_frame_in_axes
from scivianna.interface.med_interface import MEDInterface

from scivianna_example.mandelbrot.mandelbrot import MandelBrotInterface


def test_plot_grid():
    """Simple test to make sure things happen before more tests are actually implemented
    """

    # Field example
    slave = ComputeSlave(MandelBrotInterface)

    fig, axes = plt.subplots(1, 1, figsize=(8, 7))

    plot_frame_in_axes(
        slave,
        u=X,
        v=Y,
        u_min=-1.0,
        u_max=1.0,
        v_min=-1.0,
        v_max=1.0,
        u_steps=50,
        v_steps=50,
        w_value=0.0,
        coloring_label=MATERIAL,
        color_map="viridis",
        axes=axes,
        options = {"Max iter":20}
    )

    slave.terminate()

if __name__ == "__main__":
    test_plot_grid()