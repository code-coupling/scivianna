import panel as pn
import scivianna
from scivianna.constants import GEOMETRY
import pyvista as pv
from pathlib import Path
import numpy as np

from scivianna.component.r3f_component.app import ReactThreeFiber
from scivianna.interface.med_interface import MEDInterface
from scivianna.utils.color_tools import get_edges_colors, interpolate_cmap_at_values, color_maps


def get_panel(**kwargs):
    print("Reading file")
    med = MEDInterface()

    med.read_file(
        str(Path(scivianna.__file__).parent / "input_file" / "power.med"), GEOMETRY
    )
    mesh = med.mesh

    med.compute_3D_data(0., 0., 0., 0., 0., 0., None, {})

    cell_values = list(
        med.get_value_dict(
            "INTEGRATED_POWER", list(range(mesh.getNumberOfCells())), {}
        ).values()
    )

    nodes = mesh.getCoords().toNumPyArray()
    mesh.convertAllToPoly()

    print("Extracting cells")
    connectivity = mesh.getNodalConnectivity().toNumPyArray()
    indexes = mesh.getNodalConnectivityIndex().toNumPyArray()

    shapes = []
    for cell_id in range(med.mesh.getNumberOfCells()):
        i = indexes[cell_id]
        j = indexes[cell_id + 1]
        shapes.append(connectivity[i + 1: j])

    def split_list(lst, separator):
        result = []
        current = []
        for item in lst:
            if item == separator:
                if current:
                    result.append(current)
                    current = []
            else:
                current.append(item)
        if current:
            result.append(current)
        return result

    faces = [split_list(shapes[c], -1) for c in range(len(shapes))]

    print("Building polydata")

    polyhedron_connectivity = [
        # len(shapes)
        # Cell count,
        # For each cell
        #     Number of faces
        #       For each face
        #           Number of point per face
        #           List of indexes
    ]

    cell_count = min(50000, len(shapes))

    for c in range(cell_count):
        faces_med = np.array(split_list(shapes[c], -1))
        faces = np.concatenate(
            [[[faces_med.shape[1]]] * faces_med.shape[0], faces_med], axis=1
        ).flatten()

        polyhedron_connectivity += [len(faces) + 1, len(faces_med)] + faces.tolist()

    grid = pv.UnstructuredGrid(
        polyhedron_connectivity,
        [pv.celltype.CellType.POLYHEDRON for _ in range(cell_count)],
        nodes,
    )

    grid["cell_id"] = list(range(grid.GetNumberOfCells()))

    print("Building unstructured")

    def rgb_to_html(rgb):
        return [e / 255.0 for e in rgb]

    colors = interpolate_cmap_at_values(
        "BuRd", np.array(cell_values) / max(cell_values)
    )
    edge_colors = get_edges_colors(colors)

    rtf = ReactThreeFiber(
        sizing_mode="stretch_both",
        display_color_map=True,
        color_map_colors=color_maps["BuRd"],
        slice_tool_visible=True
    )

    rtf.plot_unstructured_grid(
        grid,
        colors=[rgb_to_html(list(c)) for c in colors][:cell_count],
        edge_colors=[rgb_to_html(list(c)) for c in edge_colors][:cell_count],
        values=cell_values[:cell_count],
        names=list(range(cell_count)),
    )

    return rtf


# get_panel()
if __name__ == "__main__":
    get_panel().show()

    exit()
    import socket
    import subprocess

    script_dir = Path(scivianna.component.r3f_component.__file__).parent
    p = subprocess.Popen(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", "./test.ps1"],
        cwd=script_dir,
    )
    p.wait()

    ip_adress = socket.gethostbyname(socket.gethostname())

    """
        Catching a free port to provide to pn.serve
    """
    sock = socket.socket()
    sock.bind((ip_adress, 0))
    port = sock.getsockname()[1]
    sock.close()

    pn.serve(
        get_panel,
        address=ip_adress,
        websocket_origin=f"{ip_adress}:{port}",
        port=port,
        threaded=True,
    )
