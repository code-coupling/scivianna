from scivianna.layout.split import (
    SplitItem,
    SplitDirection,
    SplitLayout,
)
from scivianna.notebook_tools import get_med_panel, _serve_panel

import panel as pn


def get_panel(_) -> SplitLayout:

    med_1 = get_med_panel(geo=None, title="MEDCoupling visualizer 1")
    med_2 = get_med_panel(geo=None, title="MEDCoupling visualizer 2")
    med_3 = get_med_panel(geo=None, title="MEDCoupling visualizer 3")

    split = SplitItem(med_1, med_2, SplitDirection.VERTICAL)
    split = SplitItem(split, med_3, SplitDirection.HORIZONTAL)

    return SplitLayout(split)


def get_template():
    panel:SplitLayout = get_panel()
    return pn.template.BootstrapTemplate(
        main=[
            pn.Column(
                panel.bounds_row,
                panel.main_frame,
                height_policy="max",
                width_policy="max",
                margin=0,
            )
        ],
        sidebar=[panel.side_bar],
        title="Split item demo",
    )


if __name__ == "__main__":
    _serve_panel(get_panel_function=get_panel)
else:
    panel:SplitLayout = get_panel()
    #   Providing servable panel, file executed with a command : "python -m panel serve my_file.py"
    panel.side_bar.servable(area="sidebar")

    pn.Column(
        panel.bounds_row, panel.main_frame, height_policy="max", width_policy="max"
    ).servable(area="main")
