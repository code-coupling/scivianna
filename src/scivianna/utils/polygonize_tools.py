import math
from typing import Any, Dict, List, Tuple, Type, Union
import numpy as np

import rasterio
import rasterio.features
from rasterio.transform import Affine 
from shapely.geometry.polygon import Polygon
from shapely.geometry import shape

class PolygonCoords:
    """Object ontaining the X and Y coordinates of a polygon
    """
    def __init__(self, 
                    x_coords:Union[List[float], np.ndarray], 
                    y_coords:Union[List[float], np.ndarray]):
        """PolygonCoords object constructor.

        Parameters
        ----------
        x_coords : Union[List[float], np.ndarray]
            X coordinates of the polygon vertices
        y_coords : Union[List[float], np.ndarray]
            Y coordinates of the polygon vertices
        """
        
        self.x_coords:Union[List[float], np.ndarray] = x_coords
        """ X coordinate of each vertex of a polygon
        """
        self.y_coords:Union[List[float], np.ndarray] = y_coords
        """ Y coordinate of each vertex of a polygon
        """

class PolygonElement:
    """Object containing the exterior polygon and the holes of a polygonal object
    """
    def __init__(self, 
                    exterior_polygon:PolygonCoords, 
                    holes:List[PolygonCoords], 
                    volume_id:str):
        """PolygonCoords object constructor.

        Parameters
        ----------
        exterior_polygon : PolygonCoords
            Polygon that surrounds a polygonal object
        holes : List[PolygonCoords]
            List of polygonal holes in a polygon object
        volume_id : str
            Volume, associated to the polygon, id
        """
    
        self.exterior_polygon:PolygonCoords = exterior_polygon
        """ Polygon that surrounds a polygonal object
        """
        self.holes:List[PolygonCoords] = holes
        """ List of polygonal holes in a polygon object
        """
        self.volume_id:str = volume_id
        """ Volume, associated to the polygon, id
        """
        self.compo:str = ""
        """ Composition in the polygon
        """

def numpy_2D_array_to_polygons(x:Union[List[float], np.ndarray], 
                                    y:Union[List[float], np.ndarray], 
                                    arr:np.ndarray, 
                                    simplify:bool) -> List[PolygonElement]:
    """Converts a 2D array mapping the volume id to a list of PolygonElements using the python module rasterio

    Parameters
    ----------
    x : Union[List[float], np.ndarray]
        Points coordinates along the X axis
    y : Union[List[float], np.ndarray]
        Points coordinates along the Y acis
    arr : np.ndarray
        2D volume index mapping
    simplify : bool
        Simplify the polygons to smoothen the edges

    Returns
    -------
    List[PolygonElement]
        List of PolygonElements
    """
    x0 = min(x)
    x1 = max(x)
    y0 = min(y)
    y1 = max(y)

    # Simplify tolerance
    delta = math.sqrt(math.pow(x[1] - x[0], 2) + math.pow(y[1] - y[0], 2))

    polygon_element_list:List[PolygonElement] = []

    transform1 = Affine.translation(x0 - (x1-x0)/len(x) / 2, y0 - (y1-y0)/len(y) / 2) * Affine.scale((x1-x0)/len(x), (y1-y0)/len(y))
    shape_gen = ((shape(s), val) for s, val in rasterio.features.shapes(arr.astype(np.int32), transform=transform1))

    s:Polygon
    for s, val in shape_gen:
        #   Checking the polygons of value 1
        if simplify:
            s = s.simplify(delta)
        polygon_element_list.append(
                        PolygonElement(exterior_polygon=PolygonCoords(x_coords=np.array([vert[0] for vert in s.exterior.coords]), 
                                                                    y_coords=np.array([vert[1] for vert in s.exterior.coords])),
                                        holes=[PolygonCoords(x_coords=np.array([vert[0] for vert in interior.coords]),
                                                             y_coords=np.array([vert[1] for vert in interior.coords])) 
                                                             for interior in s.interiors],
                                        volume_id=str(int(val)))
                    )
        
    return polygon_element_list


class PolygonSorter:
    """Object used to convert a list of polygons to shapes that are understood by Bokeh plotters
    """
    def __init__(self):
        """Object used to convert a list of polygons to shapes that are understood by Bokeh plotters
        """
        self.sort_indexes = None

    def sort_polygon_list(self,
                            polygon_list:List[PolygonElement], 
                            dict_compos_found:Dict[Union[int, str], str], 
                            dict_volume_color:Dict[Union[int, str], Tuple[float, float, float]], 
                            sort=True) \
                                -> Tuple[
                                            List[Polygon], 
                                            List[str],
                                            List[Tuple[int, int, int]]
                                        ]:
            """Converts a set of polygons to objects lists that can be understood by the panel interface

            Parameters
            ----------
            polygon_list : List[PolygonElement]
                Polygon element list from which extract the vertices coordinates
            dict_compos_found : Dict[Union[int, str], str]
                Volume - Material map
            dict_volume_color : Dict[Union[int, str], Tuple[float, float, float]]
                Volume - color map
            sort : bool
                Sort the shapes per compo

            Returns
            -------
            Tuple[List[Polygon], List[str], List[Tuple[int, int, int]]]
                List of polygons, list of compositions, list of volume colors.
            """
            
            volume_list:List[Union[str, int]] = [p.volume_id for p in polygon_list]
            compo_list:List[str] = [dict_compos_found[v] for v in volume_list]

            volume_color_list:List[Tuple[int, int, int]] = [dict_volume_color[v] for v in volume_list]
            
            # Sorting the polygons per color in order to prevent overlaping edges of different colors
            # Check if both sort and sort_indexes is None in case a slave is used for different panels.
            if self.sort_indexes is None or sort:
                self.sort_indexes = sorted(range(len(compo_list)), key=lambda i:compo_list[i])
                compo_list = [compo_list[i] for i in self.sort_indexes]
                volume_color_list = [volume_color_list[i] for i in self.sort_indexes]
                
                polygon_list = [polygon_list[i] for i in self.sort_indexes]

            return polygon_list, compo_list, volume_color_list

    def sort_list(self, arr:List[Any]) -> List[Any]:
        """Sort the array in the same order as the past polygon_element_list_to_shapes order

        Parameters
        ----------
        arr : List[Any]
            List to sort

        Returns
        -------
        List[Any]
            Sorted list
        """
        assert self.sort_indexes is not None, "The sort_list function can't be called before polygon_element_to_list_shapes is called."
        assert len(arr) == len(self.sort_indexes), f"Given array to sort has a different length from the sorted indexes, respectively found {len(arr)} and {len(self.sort_indexes)}."
        return [arr[i] for i in self.sort_indexes]
        