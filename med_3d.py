import panel as pn
import scivianna
from scivianna.constants import GEOMETRY
import cadquery as cq
import pyvista as pv
from pathlib import Path
import numpy as np
import time

from vtkmodules.vtkCommonCore import vtkCommand
from vtkmodules.vtkInteractionWidgets import vtkHoverWidget
from vtkmodules.vtkRenderingCore import vtkPointPicker, vtkCellPicker
from vtkmodules.vtkCommonDataModel import vtkCellArray

from scivianna.interface.med_interface import MEDInterface

def get_panel(**kwargs):
    med = MEDInterface()

    med.read_file(
        str(Path(scivianna.__file__).parent / "default_jdd" / "power.med"), GEOMETRY
    )
    mesh = med.mesh

    cell_values = med.get_value_dict(
        "INTEGRATED_POWER", list(range(mesh.getNumberOfCells())), {}
    )

    nodes = mesh.getCoords().toNumPyArray()
    mesh.convertAllToPoly()

    connectivity = mesh.getNodalConnectivity().toNumPyArray()
    indexes = mesh.getNodalConnectivityIndex().toNumPyArray()

    shapes = []
    for cell_id in range(med.mesh.getNumberOfCells()):
        i = indexes[cell_id]
        j = indexes[cell_id + 1]
        shapes.append(connectivity[i + 1 : j])


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


    plotter = pv.Plotter()
    cubes = []

    for c in range(len(shapes)):
        faces_med = np.array(split_list(shapes[c], -1))

        node_indexes, inv = np.unique(faces_med.flatten(), return_inverse=True)
        node_ = np.arange(len(node_indexes))

        verts = nodes[node_indexes]
        faces_arr = inv.reshape(faces_med.shape)

        faces = np.concatenate(
            [[[faces_arr.shape[1]]] * faces_arr.shape[0], faces_arr], axis=1
        ).flatten()

        cube = pv.PolyData(verts, faces)

        val = cell_values[str(c)]

        cubes += [(cube, f"Cube - {c}", (int(255 * val), int(255 * (1 - val)), 125), 0.5)]

    merged_cubes = pv.merge([c[0] for c in cubes], merge_points=True)
    merged_cubes.field_data["name"] = np.array([f"Med mesh"])
    merged_cubes.cell_data["colors"] = [c[2] for c in cubes for _ in range(6)]

    plotter.add_mesh(
        merged_cubes, 
        name=f"Med mesh", 
        scalars="colors",
        opacity = 0.5
    )


    picker = vtkCellPicker()


    def callback(_widget, event_name):
        x, y = plotter.iren.interactor.GetEventPosition()
        renderer = plotter.iren.get_poked_renderer(x, y)
        picker.Pick(x, y, 0, renderer)
        point_idx = picker.GetPointId()
        mesh = picker.GetDataSet()

        loc2 = picker.GetPickPosition()

        if mesh is not None:
            plotter.add_point_labels(
                loc2,
                [
                    mesh.field_data["name"][0]
                    + "\n"
                    + str(tuple(round(num, 2) for num in loc2))
                ],
                shape_opacity=0.1,
                name="mouse_position_label",
                pickable=False,
            )


    # hw = vtkHoverWidget()
    # hw.SetInteractor(plotter.iren.interactor)
    # hw.SetTimerDuration(1)  # Time (ms) required to trigger a hover event
    # hw.AddObserver(vtkCommand.TimerEvent, callback)  # Start of hover
    # # hw.AddObserver(vtkCommand.HoverEvent, callback)  # Start of hover
    # hw.AddObserver(vtkCommand.EndInteractionEvent, callback)  # Hover ended (mouse moved)
    # hw.EnabledOn()

    # _ = plotter.add_mesh_slice(merged_cubes, 
    #                             normal=[1, 0, 0.3]
    #                             ,outline_opacity = 0.5)

    return pn.pane.VTK(plotter.render_window, sizing_mode="stretch_both")

import socket

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