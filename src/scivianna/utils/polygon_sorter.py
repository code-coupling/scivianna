
from typing import List, Union

from scivianna.data import Data2D, DataType


class PolygonSorter:
    """Object used to sort a list of polygons per field
    """
    def __init__(self):
        """Object used to sort a list of polygons per field
        """
        self.sort_indexes = None

    def sort_polygon_list(self,
                            data:Data2D, 
                            sort=True):
            """Sorts a set of polygons per field

            Parameters
            ----------
            data : Data2D
                Data2D object containing the geometry properties
            sort : bool
                Sort the shapes per compo
            """
            values_list:List[Union[int, str]] = data.cell_values

            assert len(data.cell_values) == len(data.cell_colors), "The Data2D object must have the same number of cell values and colors"
            if data.data_type == DataType.POLYGONS:
                assert len(data.cell_values) == len(data.polygons), "The Data2D object must have the same number of cell values and polygons"

            # Sorting the polygons per color in order to prevent overlaping edges of different colors
            # Check if both sort and sort_indexes is None in case a slave is used for different panels.
            if self.sort_indexes is None or sort:
                self.sort_indexes = sorted(range(len(values_list)), key=lambda i:values_list[i])
                data.cell_ids = [data.cell_ids[i] for i in self.sort_indexes]
                data.cell_values = [values_list[i] for i in self.sort_indexes]
                data.cell_colors = [data.cell_colors[i] for i in self.sort_indexes]
                
                if data.data_type == DataType.POLYGONS:
                    data.polygons = [data.polygons[i] for i in self.sort_indexes]


    def sort_list(self, data:Data2D):
        """Sort the value and color list of a Data2D object in the same order as the past sort_polygon_list order

        Parameters
        ----------
        arr : List[Any]
            List to sort
        """
        assert self.sort_indexes is not None, "The sort_list function can't be called before polygon_element_to_list_shapes is called."
        assert len(data.cell_values) == len(self.sort_indexes), f"Given cell values list has a different length from the sorted indexes, respectively found {len(data.cell_values)} and {len(self.sort_indexes)}."
        assert len(data.cell_colors) == len(self.sort_indexes), f"Given cell colors list has a different length from the sorted indexes, respectively found {len(data.cell_colors)} and {len(self.sort_indexes)}."
        assert len(data.cell_ids) == len(self.sort_indexes), f"Given cell ID list has a different length from the sorted indexes, respectively found {len(data.cell_ids)} and {len(self.sort_indexes)}."
        data.cell_ids = [data.cell_ids[i] for i in self.sort_indexes]
        data.cell_colors = [data.cell_colors[i] for i in self.sort_indexes]
        data.cell_values = [data.cell_values[i] for i in self.sort_indexes]
        