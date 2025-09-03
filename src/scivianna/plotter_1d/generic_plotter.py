
import pandas as pd
from typing import List


class Plotter1D:
    """Unfinished 1D plotter to get the coupling working"""

    def __init__(
        self,
    ):
        pass

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
        raise NotImplementedError()
    
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
        raise NotImplementedError()
    
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
        raise NotImplementedError()

    def _disable_interactions(self, val: bool):
        pass

    def make_panel(self,):
        raise NotImplementedError()