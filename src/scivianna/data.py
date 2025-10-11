from typing import Callable, Dict, List, Any, Tuple, Union
import numpy as np
from scivianna.utils.polygonize_tools import PolygonElement, numpy_2D_array_to_polygons
from scivianna.enums import DataType


class Data2D:
    """Data class containing the 2D geometry data"""

    data_type:DataType
    """Whether the data are provided from a polygon list or a grid"""

    polygons:List[PolygonElement]
    """List of polygons defining the geometry"""

    grid:np.ndarray
    """2D grid defining the geometry"""
    u_values:np.ndarray
    """Coordinates of the grid points on the horizontal axis"""
    v_values:np.ndarray
    """Coordinates of the grid points on the vertical axis"""

    cell_ids:List[Union[int, str]]
    """List of contained cell ids"""
    cell_values:List[Union[float, str]]
    """List of contained cell values"""
    cell_colors:List[Tuple[int, int, int]]
    """List of contained cell colors"""
    
    simplify:bool
    """Simplify the polygons when converting from grid to polygon list"""

    def __init__(self):
        """ Empty constructor of the Data2D class.
        """
        self.data_type = None
        self.polygons = []
        self.grid = np.array([])
        self.u_values = np.array([])
        self.v_values = np.array([])
        self.cell_ids = []
        self.cell_values = []
        self.cell_colors = []
        self.simplify = None

    @classmethod
    def from_polygon_list(cls, polygon_list:List[PolygonElement]):
        """Build a Data2D object from a list of PolygonElement

        Parameters
        ----------
        polygon_list : List[PolygonElement]
            Polygons contained in the Data2D

        Returns
        -------
        Data2D
            Requested Data2D
        """
        data_ = Data2D()
        data_.polygons = polygon_list

        data_.cell_ids = [p.volume_id for p in polygon_list]
        data_.cell_values = [np.NaN]*len(polygon_list)
        
        data_.data_type = DataType.POLYGONS

        return data_

    @classmethod
    def from_grid(cls, grid:np.ndarray, u_values:np.ndarray, v_values:np.ndarray, simplify:bool = False):
        """Build a Data2D object from a list of PolygonElement

        Parameters
        ----------
        grid : np.ndarray
            Numpy 2D array defining the 2D geometry
        u_values : np.ndarray
            Coordinates of the grid points on the horizontal axis
        v_values : np.ndarray
            Coordinates of the grid points on the vertical axis
        simplify : bool
            Simplify the polygons when converted to polygon list

        Returns
        -------
        Data2D
            Requested Data2D
        """
        assert len(grid.shape) == 2, f"Provided grid mush be of dimension 2, found shape {grid.shape}"
        data_ = Data2D()
        data_.grid = grid
        data_.u_values = u_values
        data_.v_values = v_values

        data_.cell_ids = np.unique(grid.flatten())
        data_.cell_values = [np.NaN]*len(data_.cell_ids)

        data_.simplify = simplify
        data_.data_type = DataType.GRID

        return data_
    
    def convert_to_polygons(self,):
        """Convert the geometry to polygons
        """
        if self.data_type == DataType.POLYGONS:
            pass
        else:
            self.polygons = numpy_2D_array_to_polygons(self.u_values, self.v_values, self.grid, self.simplify)

            # The polygons count will become different than the number of cell values, so we update and change the data_type
            id_to_value = dict(zip(self.cell_ids, self.cell_values))
            id_to_color = dict(zip(self.cell_ids, self.cell_colors))

            self.cell_ids = [p.volume_id for p in self.polygons]
            self.cell_values = [id_to_value[e] for e in self.cell_ids]
            self.cell_colors = [id_to_color[e] for e in self.cell_ids]

            self.data_type = DataType.POLYGONS

    def get_polygons(self,) -> List[PolygonElement]:
        """Returns the polygon list of the geometry. If defined as grid, the grid is rasterized and self is converted to polygon data.

        Returns
        -------
        List[PolygonElement]
            Polygon list
        """
        if self.data_type == DataType.POLYGONS:
            return self.polygons
        else:
            self.convert_to_polygons()
            
            return self.polygons

    def get_grid(self,) -> np.ndarray:
        """Returns the grid associated to the current geometry

        Returns
        -------
        np.ndarray
            Geometry as a 2D grid

        Raises
        ------
        NotImplementedError
            Grid extraction from polygon list not implemented yet.
        """
        if self.data_type == DataType.POLYGONS:
            raise NotImplementedError()
        else:
            return self.grid
        
    def copy(self,) -> "Data2D":
        """Returns a copy of self

        Returns
        -------
        Data2D
            Identical copy of self
        """
        data2D = Data2D()
        data2D.data_type = self.data_type
        data2D.polygons = self.polygons.copy()
        data2D.grid = self.grid.copy()
        data2D.u_values = self.u_values.copy()
        data2D.v_values = self.v_values.copy()
        data2D.cell_ids = np.array(self.cell_ids).tolist()
        data2D.cell_values = np.array(self.cell_values).tolist()
        data2D.cell_colors = np.array(self.cell_colors).tolist()
        data2D.simplify = self.simplify

        return data2D