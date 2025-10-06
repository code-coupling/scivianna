
from typing import Any, Dict, List, Tuple, Union
import geopandas as gp
import shapely
import multiprocessing as mp
from pathlib import Path
import numpy as np

from scivianna.interface.generic_interface import GenericInterface, Geometry2DPolygon
from scivianna.constants import CSV, GEOMETRY, MATERIAL, MESH
from scivianna.slave import ComputeSlave
from scivianna.panel.plot_panel import VisualizationPanel
from scivianna.interface import csv_result
from scivianna.utils.polygonize_tools import PolygonCoords, PolygonElement
from scivianna.enums import GeometryType, UpdateEvent, VisualizationMode
from scivianna.layout.split import SplitLayout, SplitItem, SplitDirection
from scivianna.panel.line_plot_panel import LineVisualisationPanel
from scivianna.data import Data2D

from scivianna_example.europe_grid.country_time_series import CountryTimeSeriesInterface

country_cat = {
    "European Union (EU)": ["BE", "EL", "LT", "PT", "BG", "ES", "LU", "RO", "CZ", "FR", "HU", "SI", "DK", "HR", "MT", "SK", "DE", "IT", "NL", "FI", "EE", "CY", "AT", "SE", "IE", "LV", "PL"],
    "European Free Trade Association (EFTA)": ["IS", "LI", "NO", "CH"],
    "EU candidate countries": ["BA", "ME", "MD", "MK", "GE", "AL", "RS", "TR", "UA",],
    "Potential candidates": ["XK"],
    "East countries": ["AM", "BY", "AZ"],
    "European Neighbourhood Policy (ENP)-South countries": ["DZ", "LB","SY","EG", "LY","TN","IL", "MA","JO","PS"],
    "Other countries":["AR","AU","BR","CA","CN_X_HK","HK","IN","JP","MX","NG","NZ","RU","SG","ZA","KR","TW","UK","US",]	
}


def get_country_category(country_code: str):
    for cat in country_cat:
        if country_code in country_cat[cat]:
            return cat
    return np.NaN


class EuropeGridInterface(Geometry2DPolygon):
    geometry_type: GeometryType = GeometryType._2D

    def __init__(
        self,
        geometry_path: str = str(Path(__file__).parent / 'europe.geojson'),
        results: Dict[str, GenericInterface] = {},
    ):
        """Antares interface constructor."""
        self.polygons = None
        self.results = results
        if geometry_path != "":
            self.read_file(geometry_path, GEOMETRY)

    def read_file(self, file_path: str, file_label: str):
        """Read a file and store its content in the interface

        Parameters
        ----------
        file_path : str
            File to read
        file_label : str
            Label to define the file type
        """
        if file_label == GEOMETRY:
            print("Input deck file to read", file_path)

            # Geojson file downloaded from https://gisco-services.ec.europa.eu/distribution/v1/countries-2024.html
            self.data = gp.read_file(file_path)
            self.country_id = self.data["CNTR_ID"]

            self.polygons_per_country: Dict[str, List[shapely.Polygon]] = {}

            for country in range(len(self.data.count_geometries())):
                self.polygons_per_country[country] = []

                for i in range(self.data.count_geometries()[country]):
                    self.polygons_per_country[country].append(self.data.get_geometry(i)[country])

            xs_dict = [
                [
                    {
                        "exterior": p.exterior.xy[0],
                        "holes": [h.xy[0] for h in p.interiors]
                    }
                    for p in self.polygons_per_country[c]]
                for c in self.polygons_per_country
            ]

            ys_dict = [
                [
                    {
                        "exterior": p.exterior.xy[1],
                        "holes": [h.xy[1] for h in p.interiors]
                    }
                    for p in self.polygons_per_country[c]]
                for c in self.polygons_per_country
            ]

            self.xs = [[[p["exterior"], *p["holes"]] for p in mp] for mp in xs_dict]
            self.ys = [[[p["exterior"], *p["holes"]] for p in mp] for mp in ys_dict]

            self.country_list = self.data["NAME_ENGL"]

            # https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Glossary:Country_codes
            self.europe = [get_country_category(code) for code in self.country_id]

        elif file_label == CSV:
            name = Path(file_path).name
            self.results[name] = csv_result.CSVInterface(file_path)

        elif file_label == "TimeSeries":
            name = Path(file_path).name
            self.results[file_label] = CountryTimeSeriesInterface()
            self.results[file_label].read_file(file_path, file_label)
        else:
            raise NotImplementedError(
                f"File label {file_label} not implemented in Apollo3 interface."
            )

    def compute_2D_data(
        self,
        u: Tuple[float, float, float],
        v: Tuple[float, float, float],
        u_min: float,
        u_max: float,
        v_min: float,
        v_max: float,
        u_steps: int,
        v_steps: int,
        w_value: float,
        q_tasks: mp.Queue,
        options: Dict[str, Any],
    ) -> Tuple[List[PolygonElement], bool]:
        """Returns a list of polygons that defines the geometry in a given frame

        Parameters
        ----------
        u : Tuple[float, float, float]
            Horizontal coordinate director vector
        v : Tuple[float, float, float]
            Vertical coordinate director vector
        u_min : float
            Lower bound value along the u axis
        u_max : float
            Upper bound value along the u axis
        v_min : float
            Lower bound value along the v axis
        v_max : float
            Upper bound value along the v axis
        u_steps : int
            Number of points along the u axis
        v_steps : int
            Number of points along the v axis
        w_value : float
            Value along the u ^ v axis
        q_tasks : mp.Queue
            Queue from which get orders from the master.
        options : Dict[str, Any]
            Additional options for frame computation.

        Returns
        -------
        List[PolygonElement]
            List of polygons to display
        bool
            Were the polygons updated compared to the past call
        """
        if self.polygons is not None:
            print("Skipping polygon computation.")
            return self.polygons, False

        list_of_polygons = [
            PolygonElement(
                exterior_polygon=PolygonCoords(
                    np.array(p.exterior.xy[0]),
                    np.array(p.exterior.xy[1])
                ),
                holes=[
                    PolygonCoords(np.array(h.xy[0]), np.array(h.xy[1]))
                    for h in p.interiors
                ],
                volume_id=self.country_id[country],
            )
            for country in self.polygons_per_country
            for p in self.polygons_per_country[country]
        ]

        self.polygons = Data2D.from_polygon_list(list_of_polygons)
        return self.polygons, True

    def get_value_dict(
        self, value_label: str, volumes: List[Union[int, str]], options: Dict[str, Any]
    ) -> Dict[Union[int, str], str]:
        """Returns a volume name - field value map for a given field name

        Parameters
        ----------
        value_label : str
            Field name to get values from
        volumes : List[Union[int,str]]
            List of volumes names
        options : Dict[str, Any]
            Additional options for frame computation.

        Returns
        -------
        Dict[Union[int,str], str]
            Field value for each requested volume names
        """
        if value_label == MATERIAL:
            dict_compo = {
                vol: self.country_list[list(self.country_id.values).index(vol)] for vol in volumes
            }
            return dict_compo

        if value_label == MESH:
            dict_compo = {str(v): np.NaN for v in volumes}
            if -1 in dict_compo:
                dict_compo[-1] = np.NaN

            return dict_compo

        if value_label == "Europe":
            dict_compo = {
                vol: self.europe[list(self.country_id.values).index(vol)] for vol in volumes
            }
            return dict_compo

        for res in self.results.values():
            if value_label in res.get_fields():
                results = res.get_values([], volumes, [self.country_id[list(self.country_id.values).index(vol)] for vol in volumes], value_label)
                return {volumes[i]: results[i] for i in range(len(volumes))}

        raise NotImplementedError(
            f"The field {value_label} is not implemented, fields available : {self.get_labels()}"
        )

    def get_labels(
        self,
    ) -> List[str]:
        """Returns a list of fields names displayable with this interface

        Returns
        -------
        List[str]
            List of fields names
        """
        labels = [MATERIAL, MESH, "Europe"]

        for res in self.results.values():
            labels += res.get_fields()

        return labels

    def get_label_coloring_mode(self, label: str) -> VisualizationMode:
        """Returns wheter the given field is colored based on a string value or a float.

        Parameters
        ----------
        label : str
            Field to color name

        Returns
        -------
        VisualizationMode
            Coloring mode
        """
        print("Requested : " + label)
        if label == MESH:
            return VisualizationMode.NONE
        if label in [MATERIAL, "Europe"]:
            return VisualizationMode.FROM_STRING
        else:
            return VisualizationMode.FROM_VALUE

    def get_file_input_list(self) -> List[Tuple[str, str]]:
        """Returns a list of file label and its description for the GUI

        Returns
        -------
        List[Tuple[str, str]]
            List of (file label, description)
        """
        return [
            (GEOMETRY, "Apollo3 .ap3 file."),
            (CSV, "CSV result file."),
        ]


def make_europe_panel(_, return_slaves: bool = False):
    slave = ComputeSlave(EuropeGridInterface)
    # Time serie CSV coming from a post processing of the data available at https://www.entsoe.eu/eraa/
    slave.read_file(str(Path(__file__).parent / "time_series.csv"), "TimeSeries")

    slave_result = ComputeSlave(CountryTimeSeriesInterface)
    slave_result.read_file(str(Path(__file__).parent / "time_series.csv"), "TimeSeries")

    map_panel = VisualizationPanel(slave, name="Map")
    map_panel.sync_field = True
    line_panel = LineVisualisationPanel(slave_result, name="Plot")
    line_panel.update_event = UpdateEvent.MOUSE_CELL_CHANGE
    line_panel.sync_field = True

    split_panel = SplitLayout(
        SplitItem(
            map_panel,
            line_panel,
            SplitDirection.VERTICAL
        ),
        additional_interfaces={"EuropeGrid": EuropeGridInterface, "TimeSeries": CountryTimeSeriesInterface},
    )

    if return_slaves:
        return split_panel, [slave, slave_result]
    else:
        return split_panel


if __name__ == "__main__":
    from scivianna.notebook_tools import _serve_panel

    _serve_panel(get_panel_function=make_europe_panel, title="Europe grid")
