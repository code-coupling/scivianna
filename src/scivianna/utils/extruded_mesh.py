from typing import Any, Dict, List, Tuple
import numpy as np
from scivianna.utils.color_tools import get_edges_colors
import shapely

try:
    import pyvista as pv
    from pyvista import core
except ImportError:
    raise ImportError(
        "Failed to import pyvista, install scivianna using the command pip install scivianna[pyvista]"
    )

from scivianna.utils.polygonize_tools import PolygonCoords, PolygonElement

class ExtrudedStructuredMesh:
    """Structured mesh build from a set of PolygonElement on the XY plane, extruded at a set of Z values
    """
    def __init__(
        self, xy_mesh: List[PolygonElement], z_coords: np.ndarray
    ):
        """Builds the mesh based on the (r, theta, phi) bins.

        Parameters
        ----------
        xy_mesh : List[PolygonElement]
            List of PolygonElement to extrude along the z axis
        z_coords : np.ndarray
            Bins on the Z axis
        """
        super().__init__()
        
        # Create structured grid
        self.base_polygons = xy_mesh
        self.z_coords = z_coords

        self.build_pyvista_geometry()
        
        self.grids:Dict[str, Dict[str, Any]] = {}

        self.past_computation = []

    def build_pyvista_geometry(self,):
        """Builds the PyVista geometry from the list of polygons
        """
        polys = {}

        count_cells = len(self.base_polygons)

        for i in range(len(self.z_coords)-1):
            z = self.z_coords[i]
            polygons = [p.to_shapely(z_coord=z) for p in self.base_polygons]

            for k in range(count_cells):
                # Convert to PyVista mesh
                cell_id = k + i*count_cells
                points = []
                faces = []

                if (len(polygons[k].interiors) == 0):
                    poly = polygons[k]
                    points = poly.exterior.coords
                    faces = [len(points)] + list(range(len(points)))
                else:
                    triangulated = shapely.constrained_delaunay_triangles(polygons[k])
                    for triangle in triangulated.geoms:
                        tri_points = np.array(triangle.exterior.coords)
                        points.extend(tri_points)

                        # Create face indices (3 for triangle)
                        face = [3] + [len(points) - 3 + i for i in range(3)]
                        faces.extend(face)

                # Create PyVista mesh
                mesh = pv.PolyData(
                    np.array(points),
                    np.array(faces, dtype=np.int32),
                ).clean()

                mesh["cell_id"] = [cell_id] * mesh.n_points
                mesh.extrude(vector=(0, 0, self.z_coords[i+1] - z), inplace=True, capping=True).clean()

                polys[cell_id] = mesh
                
        self.blocks = pv.MultiBlock(list(polys.values()))

    def set_values(self, name:str, grid:Dict[int, Any]):
        """Setting a Numpy array grid to the given name. The numpy array must be of size (nx, ny, nz) and the data are called in the XYZ order.

        Parameters
        ----------
        name : str
            Field name
        grid : np.ndarray
            Field value
        """
        self.grids[name] = grid

    def get_cells_values(self, name:str, cell_ids:List[int]) -> np.ndarray:
        """Returns a field values for a list of cell indexes

        Parameters
        ----------
        name : str
            field name
        cell_ids : List[int]
            cells indexes

        Returns
        -------
        np.ndarray
            List of values per cell

        Raises
        ------
        RuntimeError
            Requested a field before defining it
        """
        if name not in self.grids:
            raise RuntimeError(f"Field {name} is not defined. Found {list(self.grids.keys())}.")
        if len(cell_ids) == 0:
            return []
            
        return [self.grids[name][c] for c in cell_ids]

    def compute_2D_slice(
        self,
        origin: Tuple[float, float, float],
        u: Tuple[float, float, float],
        v: Tuple[float, float, float],
    ) -> List[PolygonElement]:
        """Computes the PolygonElement list for a slice of the mesh

        Parameters
        ----------
        origin : Tuple[float, float, float]
            Slice origin
        u : Tuple[float, float, float]
            First axis vector
        v : Tuple[float, float, float]
            Second axis vector

        Returns
        -------
        List[PolygonElement]
            List of polygon elements defining the cut

        Raises
        ------
        ValueError
            U and V are either parallel or one is of zero length.
        """
        if self.past_computation == [*list(u), *list(v), *list(origin)]:
            return self.polygons
        u = np.array(u)/np.linalg.norm(u)
        v = np.array(v)/np.linalg.norm(v)
        w = np.cross(u, v)

        if np.linalg.norm(w) == 0.:
            raise ValueError(f"u and v must be both non zero and non parallel, found {u}, {v}")
        
        w /= np.linalg.norm(w)

        mesh_slice: core.MultiBlock = self.blocks.slice(
            origin=origin, normal=w
        )

        blocks = [mesh_slice.get_block(i) for i in range(mesh_slice.n_blocks)]

        polygon_elements = {}

        for b in blocks:
            rings = []

            coords = np.array(b.points)
            edges = [c.point_ids for c in b.cell]
            current_loop = []
            found = False

            while len(edges) > 0:
                if current_loop == []:
                    current_loop.append(edges[0])
                    current_point = current_loop[0][1]
                    edges.remove(edges[0])
                else:
                    found = False
                    for s in edges:
                        if current_point in [s[0], s[1]]:
                            if s[1] == current_point:
                                current_loop.append([s[1], s[0]])
                                current_point = s[0]
                            else:
                                current_loop.append(s)
                                current_point = s[1]
                            edges.remove(s)
                            found = True
                            break

                    if not found:
                        rings.append(current_loop)
                        current_loop = []

            if current_loop != []:
                rings.append(current_loop)

            polys: List[shapely.Polygon] = []

            for loop in rings:
                ids = np.array([e[0] for e in loop] + [loop[-1][1]] + [loop[0][0]])

                polys.append(shapely.Polygon(shell=np.array([coords[ids].dot(u), coords[ids].dot(v)]).T, holes=[]))

            if len(polys) == 0:
                continue
                
            if len(polys) == 1:
                polygon_elements[b["cell_id"][0]] = PolygonElement(
                    PolygonCoords(
                        np.array(polys[0].exterior.coords)[:, 0], np.array(polys[0].exterior.coords)[:, 1]
                    ),
                    [],
                    b["cell_id"][0],
                )
            else:
                main = polys[0]
                holes = []
                for poly in polys[1:]:
                    if main.contains(poly):
                        holes.append(poly)
                    else:
                        holes.append(main)
                        main = poly
                        
                polygon_elements[b["cell_id"][0]] = PolygonElement(
                    PolygonCoords(
                        np.array(main.exterior.coords)[:, 0], np.array(main.exterior.coords)[:, 1]
                    ),
                    [PolygonCoords(
                        np.array(h.exterior.coords)[:, 0], np.array(h.exterior.coords)[:, 1]
                    ) for h in holes],
                    b["cell_id"][0],
                )

        self.polygons = list(polygon_elements.values())
        self.past_computation == [*list(u), *list(v), *list(origin)]
        
        return self.polygons

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    from scivianna.plotter_2d.polygon.matplotlib import Matplotlib2DPolygonPlotter
    from scivianna.data.data2d import Data2D
    from scivianna.utils.color_tools import interpolate_cmap_at_values

    
    outer_square = [(0, 0), (2, 0), (2, 2), (0, 2)]
    inner_hole = [(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5)]
    inner_hole_0 = [(0.5, 0.5), (1., 0.5), (1., 1.5), (0.5, 1.5)]
    inner_hole_1 = [(1., 0.5), (1.5, 0.5), (1.5, 1.5), (1., 1.5)]

    outer_coords = PolygonCoords(
        [e[0] for e in outer_square],
        [e[1] for e in outer_square]
    )
    
    inner_coords = PolygonCoords(
        [e[0] for e in inner_hole],
        [e[1] for e in inner_hole]
    )
    
    inner_coords_0 = PolygonCoords(
        [e[0] for e in inner_hole_0],
        [e[1] for e in inner_hole_0]
    )
    
    inner_coords_1 = PolygonCoords(
        [e[0] for e in inner_hole_1],
        [e[1] for e in inner_hole_1]
    )
    
    p0 = PolygonElement(outer_coords, [inner_coords], 0 )

    p1 = PolygonElement(inner_coords_0, [], 1)

    p2 = PolygonElement(inner_coords_1, [], 2)


    mesh = ExtrudedStructuredMesh(
        [p0, p1, p2], list(range(5))
    )
    mesh.set_values("id", {i:i for i in range(4*3)})

    polygons = mesh.compute_2D_slice((1., 1., 0.5), (1, 0, 0), (0, 1, 0))

    data = Data2D.from_polygon_list(polygons)

    data.cell_values = mesh.get_cells_values("id", [p.volume_id for p in polygons])
    data.cell_colors = interpolate_cmap_at_values("viridis", np.array(data.cell_values)/(4*3))
    data.cell_edge_colors = get_edges_colors(data.cell_colors)
    
    plotter = Matplotlib2DPolygonPlotter()
    plotter.plot_2d_frame(data)
    plotter.figure.savefig("test_extruded_0.png")
    plt.close()

    polygons = mesh.compute_2D_slice((1., 1., 0.5), (1, 0, 0), (0, 0, 1))
    data = Data2D.from_polygon_list(polygons)

    data.cell_values = mesh.get_cells_values("id", [p.volume_id for p in polygons])
    data.cell_colors = interpolate_cmap_at_values("viridis", np.array(data.cell_values)/(4*3))
    data.cell_edge_colors = get_edges_colors(data.cell_colors)

    plotter = Matplotlib2DPolygonPlotter()
    plotter.plot_2d_frame(data)
    plotter.figure.savefig("test_extruded_1.png")
    plt.close()
