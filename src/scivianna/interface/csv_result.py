import os
from pathlib import Path
import numpy as np
import pandas as pd
from typing import List, Tuple, Union
from scivianna.interface.generic_interface import ValueAtLocation


class CSVInterface(ValueAtLocation):
    def __init__(self, csv_file_path: str):
        """CSV file interface to get results from.

        Parameters
        ----------
        csv_file_path : str
            CSV file input path

        Raises
        ------
        ValueError
            File not found
        ValueError
            Neither volume nor materials in the file columns
        """
        path = Path(csv_file_path)
        self.basename = path.name.replace(".csv", "")

        if not os.path.isfile(path):
            raise ValueError(f"Provided path does not exist : {csv_file_path}.")

        self.df = pd.read_csv(path)

        if not ("material" in self.df.columns or "volume" in self.df.columns):
            raise ValueError(
                f"Neither material nor volume was found in the csv columns. Found: {self.df.columns}."
            )

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
        if field not in self.df.columns:
            raise ValueError(
                f"Field {field} not found in dataframe columns, found : {self.df.columns}."
            )

        if "volume" in self.df.columns:
            look_column = self.df["volume"]
            line_index = look_column[look_column == volume_index].index[0]

        elif "material" in self.df.columns:
            look_column = self.df["material"]
            line_index = look_column[look_column == material_name].index[0]

        else:
            raise ValueError(
                f"Neither material nor volume was found in the csv columns. Found: {self.df.columns}."
            )

        return self.df.loc[field, line_index]

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
        field = field[len(self.basename) + 1:]
        if field not in self.df.columns:
            raise ValueError(
                f"Field {field} not found in dataframe columns, found : {self.df.columns}."
            )

        if "volume" in self.df.columns:
            new_df = self.df.copy()
            new_df["volume"] = new_df["volume"].astype(str)
            new_df = new_df.set_index("volume")

            if "-1" in volume_indexes:
                list_volumes = list(volume_indexes.copy())
                list_volumes.remove("-1")
                vals = new_df[field][list_volumes].to_list()
                vals.insert(list(volume_indexes.copy()).index("-1"), np.NaN)

                return vals
            else:
                return new_df[field][volume_indexes].to_list()

        elif "material" in self.df.columns:
            new_df = self.df.copy()
            new_df["material"] = new_df["material"].astype(str)
            new_df = new_df.set_index("material")

            if "Out of geometry" in material_names:
                list_materials = list(material_names.copy())
                list_materials.remove("Out of geometry")
                vals = new_df[field][list_materials].to_list()
                vals.insert(
                    list(material_names.copy()).index("Out of geometry"), np.NaN
                )

                return vals
            else:
                return new_df[field][material_names].to_list()

        else:
            raise ValueError(
                f"Neither material nor volume was found in the csv columns. Found: {self.df.columns}."
            )

    def get_fields(self) -> List[str]:
        """Returns the fields names providable.

        Returns
        -------
        List[str]
            Fields names
        """
        return [
            self.basename + "_" + c
            for c in self.df.columns
            if c not in ["volume", "material"]
        ]
