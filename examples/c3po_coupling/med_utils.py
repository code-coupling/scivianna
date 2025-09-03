from pathlib import Path
from typing import List, Optional
import medcoupling



def list_2_med(tolist, name) -> medcoupling.MEDCouplingFieldDouble:
    """Creates a dummy med to locate core center

    Parameters
    ----------
    tolist : tuple, optional
        list to transfor to field, by default ()
    name : str, optional
        name of the field, by default ()

    Returns
    -------
    medcoupling.MEDCouplingFieldDouble
        1D field wich array is the list
    """
    mcfield = medcoupling.MEDCouplingFieldDouble(medcoupling.ON_CELLS, medcoupling.ONE_TIME)
    mcfield.setName(name)
    mcfield.setTime(0., 0, 0)
    mesh = medcoupling.MEDCouplingCMesh(f"{name}_mesh")
    mesh.setCoordsAt(0, medcoupling.DataArrayDouble(list(range(len(tolist)+1))))
    mcfield.setMesh(mesh)
    mcfield.setArray(medcoupling.DataArrayDouble(tolist))
    return mcfield


def get_field_template(name: str,
                       mesh: medcoupling.MEDCouplingUMesh,
                       array: Optional[medcoupling.DataArrayDouble] = None,
                       nature: Optional[int] = medcoupling.IntensiveMaximum
                       ) -> medcoupling.MEDCouplingFieldDouble:

    mcfield = medcoupling.MEDCouplingFieldDouble(medcoupling.ON_CELLS, medcoupling.ONE_TIME)
    mcfield.setName(name)
    mcfield.setTime(0., 0, 0)
    mcfield.setMesh(mesh)
    if array is None:
        array = medcoupling.DataArrayDouble([0.] * mesh.getNumberOfCells())
    mcfield.setArray(array)
    if nature is not None:
        mcfield.setNature(nature)
    return mcfield


def write_field(field: medcoupling.MEDCouplingField,
                file_path: Path,
                append: bool,
                share_mesh: bool = True) -> Path:
    """Write fields on file

    Parameters
    ----------
    field : medcoupling.MEDCouplingField
        Field to write
    file_path : Path
        File withe '.med' suffix.
        If suffix is not provided, it is added.
        If path is a directory, field name is used to name the file.
    append : bool
        Add the field in the file if True, else create a new file
    share_mesh : bool, optional
        True to write the mesh only at file creation, assumes append is also True, by default True

    Returns
    -------
    Path
        Final field name
    """

    if file_path.is_dir():
        file_path = file_path / field.getName()

    if file_path.suffix != ".med":
        file_path = file_path.with_suffix(".med")

    if append and share_mesh:
        if not file_path.exists():
            medcoupling.WriteUMesh(fileName=str(file_path),
                                   mesh=field.getMesh(),
                                   writeFromScratch=True)

        medcoupling.WriteFieldUsingAlreadyWrittenMesh(f=field, fileName=str(file_path))

    else:
        medcoupling.WriteField(fileName=str(file_path), writeFromScratch=not append, f=field)

    return file_path


def define_cartesian_mesh(coords_x: List[float],
                          coords_y: List[float],
                          coords_z: Optional[List[float]]) -> medcoupling.MEDCouplingUMesh:
    """Generates a 3D cartesian mesh

    Parameters
    ----------
    coords_x : List[float]
        x coordinates of the nodes (len >=2)
    coords_y : List[float]
        y coordinates of the nodes (len >=2)
    coords_z : Optional[List[float]]
        coordinates of the nodes (len >=2), if None a 2D mesh is produced


    Returns
    -------
    medcoupling.MEDCouplingUMesh
        3D cartesian mesh
    """

    ndim = 3 if coords_z is not None else 2

    nb_cells_x = len(coords_x) - 1
    nb_cells_y = len(coords_y) - 1
    nb_cells_z = len(coords_z) - 1 if ndim == 3 else 0
    nb_cells = nb_cells_x * nb_cells_y * (nb_cells_z if ndim == 3 else 1)

    coordinates = []
    for j in range(nb_cells_y):
        y_0 = coords_y[j]
        y_1 = coords_y[j + 1]

        for i in range(nb_cells_x):
            x_0 = coords_x[i]
            x_1 = coords_x[i + 1]

            if ndim == 3:
                for k in range(nb_cells_z):
                    z_0 = coords_z[k]
                    z_1 = coords_z[k + 1]
                    #      x_0        x_1
                    # y_1   __________  y_1
                    #      |          |
                    #      |          |
                    # y_0  |__________| y_0
                    #     x_0        x_1

                    coordinates += [(x_0, y_0, z_0),
                                    (x_0, y_1, z_0),
                                    (x_1, y_1, z_0),
                                    (x_1, y_0, z_0),
                                    (x_0, y_0, z_1),
                                    (x_0, y_1, z_1),
                                    (x_1, y_1, z_1),
                                    (x_1, y_0, z_1),]
            else:
                coordinates += [(x_0, y_0),
                                (x_0, y_1),
                                (x_1, y_1),
                                (x_1, y_0),]

    mesh = medcoupling.MEDCouplingUMesh(f"{ndim}d_mesh", ndim)
    mesh.setMeshDimension(ndim)
    mesh.setDescription("core mesh")
    mesh.allocateCells(nb_cells)

    if ndim == 3:
        for i_cell in range(nb_cells):
            mesh.insertNextCell(medcoupling.NORM_HEXA8, [i_cell * 8 + j for j in range(8)])
    else:
        for i_cell in range(nb_cells):
            mesh.insertNextCell(medcoupling.NORM_QUAD4, [i_cell * 4 + j for j in range(4)])

    mesh.finishInsertingCells()
    mesh.setCoords(medcoupling.DataArrayDouble(coordinates))
    mesh.checkConsistencyLight()
    return mesh

