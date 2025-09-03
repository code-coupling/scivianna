
from typing import Dict, List
import bokeh.io
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.models.renderers import GlyphRenderer
from bokeh.models.annotations import Legend, LegendItem
from bokeh.palettes import Spectral11 as palette
from bokeh.models import HoverTool

import pandas as pd
import panel as pn

from scivianna.plotter_1d.generic_plotter import Plotter1D


class BokehPlotter1D(Plotter1D):
    """Unfinished 1D plotter to get the coupling working"""

    def __init__(
        self,
    ):
        self.source_data_dict:Dict[str, ColumnDataSource] = {}
        self.line_dict:Dict[str, GlyphRenderer]= {}

        self.fig = figure(
            name="plot",
            width_policy="max",
            height_policy="max",
        )
        self.hover = HoverTool(
            tooltips="$name: (@x, @y)"

        )
        self.fig.add_tools(self.hover)

        self.fig_pane = pn.pane.Bokeh(
            self.fig,
            name="Plot",
            width_policy="max",
            height_policy="max",
            margin=0,
            styles={"border": "2px solid lightgray"},
        )

    def plot(
        self,
        name:str,
        serie: pd.Series
    ):
        """Adds a new plot to the figure from a set of polygons

        Parameters
        ----------
        name : str
            Plot name
        serie : pd.Series
            Sata to plot
        """
        self.source_data_dict[name] = ColumnDataSource(
                                            {
                                                "x": serie.index.tolist(),
                                                "y": serie.values.tolist(),
                                            }
                                        )
        self.line_dict[name] = self.fig.line(x="x", 
                        y="y", 
                        line_width=2,
                        source=self.source_data_dict[name],
                        legend_label=name,
                        name=name.replace(" ", "_"))



    def update_plot(
        self,
        name:str,
        serie: pd.Series
    ):
        """Updates plot to the figure

        Parameters
        ----------
        name : str
            Plot name
        serie : pd.Series
            Sata to plot
        """
        if name in self.source_data_dict:
            self.source_data_dict[name].update(data={
                "x":serie.index.tolist(),
                "y":serie.values.tolist(),
            })
        else:
            self.plot(name, serie)
    
    def set_visible(
        self,
        names:List[str],
    ):
        """Updates the visible plots in the figure

        Parameters
        ----------
        names : List[str]
            List of displayed plots
        """
        for glyph_name in self.line_dict:
            self.line_dict[glyph_name].visible = glyph_name in names
            if glyph_name in names:
                self.line_dict[glyph_name].glyph.line_color = palette[names.index(glyph_name)%len(palette)]

        l:Legend
        li:LegendItem
        for l in self.fig.legend:
            for li in l.items:
                if li.label.value in names:
                    li.visible = True
                else:
                    li.visible = False

        self.hover.update(renderers = [self.line_dict[glyph_name] for glyph_name in names])


    def _disable_interactions(self, val: bool):
        pass

    def make_panel(self,):
        return self.fig_pane
