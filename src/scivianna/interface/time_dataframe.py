import os
from pathlib import Path
import numpy as np
import pandas as pd
from typing import List, Tuple, Union
from scivianna.interface.generic_interface import Value1DAtLocation, IcocoInterface


class TimeDataFrame(Value1DAtLocation, IcocoInterface):
    def __init__(self, ):
        """Interface hosting a dataframe that is filled along a coupling

        """
        self.df = pd.DataFrame()
        self.time = 0.

    def get_labels(self) -> List[str]:
        """Returns the fields names providable.

        Returns
        -------
        List[str]
            Fields names
        """
        return self.df.columns.tolist()

    def get_1D_value(
        self,
        position: Tuple[float, float, float],
        volume_index: str,
        material_name: str,
        field: str,
    ) -> Union[pd.Series, List[pd.Series]]:
        """Provides the 1D value of a field from either the (x, y, z) position, the volume index, or the material name.

        Parameters
        ----------
        position : Tuple[float, float, float]
            Position at which the value is requested
        volume_index : str
            Index of the requested volume
        material_name : str
            Name of the requested material
        field : str
            Requested field name

        Returns
        -------
        Union[pd.Series, List[pd.Series]]
            Field value
        """
        if field in self.df.columns:
            return self.df[field]
        else:
            raise ValueError(f"Field {field} not found, dataframe contains {self.df.columns.tolist()}")
    
    def setTime(self, time:float):
        """This non-Icoco function allows setting the current time in an interface to associate to the received value.

        Parameters
        ----------
        time : float
            Current time
        """
        self.time = time

        if not time in self.df.index:
            self.df = pd.concat([
                self.df,
                pd.DataFrame({
                    col:[np.NaN] for col in self.df.columns
                }, index = [self.time])
            ])

    def setInputDoubleValue(self, name: str, val: float) -> None:
        """(Optional) Provide the code with a scalar double data.

        See Problem documentation for more details on the time semantic of a scalar value.

        Parameters
        ----------
        name : str
            name of the scalar value that is given to the code.
        val : float
            value passed to the code.

        Raises
        ------
        WrongArgument
            exception if the scalar name ('name' parameter) is invalid.
        WrongContext
            exception if called before initialize() or after terminate().
        """
        if not name in self.df.columns:
            self.df.loc[:,name] = pd.Series([np.NaN]*len(self.df), index=self.df.index)

        self.df.loc[self.time, name] = val

