import panel as pn
import scivianna
from scivianna.constants import GEOMETRY
import pyvista as pv
from pathlib import Path
import numpy as np

from scivianna.components.r3f_component.app import ReactThreeFiber
from scivianna.interface.med_interface import MEDInterface
from scivianna.utils.color_tools import get_edges_colors, interpolate_cmap_at_values


def get_panel(**kwargs):
    med = MEDInterface()

    med.read_file(
        str(Path(scivianna.__file__).parent / "default_jdd" / "power.med"), GEOMETRY
    )
    mesh = med.mesh

    cell_values = list(
        med.get_value_dict(
            "INTEGRATED_POWER", list(range(mesh.getNumberOfCells())), {}
        ).values()
    )

    nodes = mesh.getCoords().toNumPyArray()
    mesh.convertAllToPoly()

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

    per_cell_verts = []
    per_cell_faces = []

    list_objects = []

    for c in range(len(shapes)):
        faces_med = np.array(split_list(shapes[c], -1))
        #     print(faces_med)

        node_indexes, inv = np.unique(faces_med.flatten(), return_inverse=True)

        verts = nodes[node_indexes]
        faces_arr = inv.reshape(faces_med.shape)

        faces = np.concatenate(
            [[[faces_arr.shape[1]]] * faces_arr.shape[0], faces_arr], axis=1
        ).flatten()

        cube = pv.PolyData(verts, faces)
        cube.triangulate(pass_verts=True, inplace=True)
        cube["cell_id"] = [c] * cube.n_points

        faces = cube.faces
        per_cell_verts.append(cube.points.tolist())
        per_cell_faces.append(
            [list(faces[1 + 4 * i: 4 + 4 * i]) for i in range(int(len(faces) / 4))]
        )

        list_objects += [cube]

    multi_block = pv.MultiBlock(list_objects)

    def rgb_to_html(rgb):
        return [e / 255.0 for e in rgb]

    colors = interpolate_cmap_at_values(
        "BuRd", np.array(cell_values) / max(cell_values)
    )
    edge_colors = get_edges_colors(colors)

    count = len(colors)
    max_val = count
    return ReactThreeFiber(
        multi_block=multi_block[:max_val],
        # vertices=per_cell_verts[0: int(count / 2)],
        # objects=per_cell_faces[0: int(count / 2)],
        colors=[rgb_to_html(list(c)) for c in colors][:max_val],
        edge_colors=[rgb_to_html(list(c)) for c in edge_colors][:max_val],
        values=cell_values[:max_val],
        names=list(range(len(cell_values)))[:max_val],
        sizing_mode="stretch_both",
    )


# get_panel()
if __name__ == "__main__":
    import socket
    import subprocess

    script_dir = Path(scivianna.components.r3f_component.__file__).parent
    p = subprocess.Popen(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", "./test.ps1"],
        cwd=script_dir
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
