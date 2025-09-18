from scivianna_example.europe_grid.europe_grid import (
    make_europe_panel as europe_example,
)
import scivianna_example.europe_grid.europe_grid as europe_grid
from scivianna_example.medcoupling.split_item_example import (
    get_panel as medcoupling_example,
)
import scivianna_example.medcoupling.split_item_example as split_item_example

from pathlib import Path

import panel_material_ui as pmui


def make_demo(return_slaves = False) -> pmui.Page:
    if return_slaves:
        europe_panel, slaves_europe = europe_example(None, return_slaves)
        medcoupling_panel, slaves_medcoupling = medcoupling_example(None, return_slaves)
    else:
        europe_panel = europe_example(None)
        medcoupling_panel = medcoupling_example(None)

    with open(Path(europe_grid.__file__).parent / "description.md", "r") as f:
        europe_with_description = pmui.Row(
            europe_panel.main_frame, 
            pmui.Typography(f.read(), width=300)
        )

    with open(Path(split_item_example.__file__).parent / "description.md", "r") as f:
        medcoupling_with_description = pmui.Row(
            medcoupling_panel.main_frame, 
            pmui.Typography(f.read(), width=300)
        )
    sidebars = [
            europe_panel.side_bar,
            medcoupling_panel.side_bar,
        ]
    
    tabs = pmui.Tabs(
        ("Europe example", europe_with_description),
        ("Medcoupling example", medcoupling_with_description),
    )
    
    def change_active(e):
        for sidebar in sidebars:
            sidebar.visible = (tabs.active == sidebars.index(sidebar))

    tabs.param.watch(change_active, "active")
    change_active(None)

    page = pmui.Page(
        main=[tabs],
        sidebar=sidebars,
        sidebar_variant="temporary",
        sidebar_open=False,
        title="Scivianna demonstrator"
    )

    if return_slaves:
        return page, slaves_medcoupling+slaves_europe
    else:
        return page


if __name__ == "__main__":
    make_demo().show()
