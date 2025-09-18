import os
from pathlib import Path
import numpy as np
import pandas as pd
from typing import List, Tuple, Union
from scivianna.interface.generic_interface import ValueAtLocation, Value1DAtLocation


class CountryTimeSeriesInterface(ValueAtLocation, Value1DAtLocation):
    def __init__(self, ):
        """CSV file interface to get results from.
        """
        pass

    def read_file(self, csv_file_path:str, file_type:str):
        """Read CSV file to get results from.

        Parameters
        ----------
        csv_file_path : str
            CSV file input path

        """
        path = Path(csv_file_path)
        self.df = pd.read_csv(path)
        
        self.country_codes = []
        self.fields = []
        for col in self.df.columns:
            if not (col.startswith("Unnamed") or col=="Time"):
                if "load" in col:
                    country_code = col[:2].upper()
                    self.country_codes.append(country_code)
                
                field_name = col[3:]
                self.fields.append(field_name)
                
        self.country_codes = list(set(self.country_codes))
        self.fields = list(set(self.fields))

    def get_value(
        self,
        position: Tuple[float, float, float],
        volume_index: str,
        material_name: str,
        field: str,
    ):
        """Provides the result value of a field from either the (x, y, z) position, the volume index, or the material name.

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
        List[Union[str, float]]
            Field value
        """
        if volume_index in self.country_codes:
            return 1.
        else:
            return 0.

    def get_values(
        self,
        positions: List[Tuple[float, float, float]],
        volume_indexes: List[str],
        material_names: List[str],
        field: str,
    ) -> List[Union[str, float]]:
        """Provides the result values at different positions from either the (x, y, z) positions, the volume indexes, or the material names.

        Parameters
        ----------
        positions : List[Tuple[float, float, float]]
            List of position at which the value is requested
        volume_indexes : List[str]
            Indexes of the requested volumes
        material_names : List[str]
            Names of the requested materials
        field : str
            Requested field name

        Returns
        -------
        List[Union[str, float]]
            Field values
        """
        output = []

        for vol_id in volume_indexes:
            if vol_id in self.country_codes:
                val = 0.

                for column in self.df.columns:
                    if column.startswith(vol_id.lower()) and column.endswith(field):
                        val += self.df[column].sum()
                output.append(val)
            else:
                output.append(np.NaN)
        return output

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
        output = None

        if volume_index in self.country_codes:
            for column in self.df.columns:
                if column.startswith(volume_index.lower()) and column.endswith(field):
                    if output is None:
                        output = self.df[column].copy()
                    else:
                        output += self.df[column]

        if output is None:         
            output = self.df["Time"].copy()*0.
            output.replace(0., np.NaN)

        output.rename(f"{volume_index}_{field}")

        return pd.Series(output)

    def get_fields(self) -> List[str]:
        """Returns the fields names providable.

        Returns
        -------
        List[str]
            Fields names
        """
        return self.fields
    
    def get_labels(self) -> List[str]:
        """Returns the fields names providable.

        Returns
        -------
        List[str]
            Fields names
        """
        return self.get_fields()

    def get_1D_fields(self) -> List[str]:
        """Returns the fields names providable.

        Returns
        -------
        List[str]
            Fields names
        """
        return self.fields