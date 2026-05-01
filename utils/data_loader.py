import os
import numpy as np
import opensim as osim
from utils.config import data_path, outputs_path, c3dFileAdapter, trcFileAdapter
from utils.helpers import rotate_markers_z_to_y, rotate_forces_z_to_y, zero_unloaded_plates, filter_forces, filter_markers


def load_static():
    static_c3d_file = next(
        (os.path.join(data_path, f) for f in os.listdir(data_path)
         if f.endswith(".c3d") and f.startswith("static")),
        None
    )
    if static_c3d_file is None:
        raise FileNotFoundError("No static*.c3d file found in data directory")

    static_tables = c3dFileAdapter.read(static_c3d_file)
    static_markersTable = c3dFileAdapter.getMarkersTable(static_tables)
    static_markersTable = rotate_markers_z_to_y(static_markersTable)
    static_markersTable = filter_markers(static_markersTable)

    trcFileAdapter.write(static_markersTable, os.path.join(outputs_path, "static_markers.trc"))

    t_start = static_markersTable.getIndependentColumn()[0]
    t_end   = static_markersTable.getIndependentColumn()[-1]

    static_forcesTable = c3dFileAdapter.getForcesTable(static_tables)
    rows = []
    for i in range(static_forcesTable.getNumRows()):
        row = static_forcesTable.getRowAtIndex(i)
        flat = []
        for j in range(row.size()):
            vec = row[j]
            flat.extend([vec[0], vec[1], vec[2]])
        rows.append(flat)

    forces_matrix = np.array(rows)
    fz_total = forces_matrix[:, 2] + forces_matrix[:, 11] + forces_matrix[:, 20]
    mass = np.mean(fz_total) / 9.81

    return mass, t_start, t_end


def load_dynamic():
    dynamic_c3d_file = next(
        (os.path.join(data_path, f) for f in os.listdir(data_path)
         if f.endswith(".c3d") and f.startswith("movement")),
        None
    )
    if dynamic_c3d_file is None:
        raise FileNotFoundError("No movement*.c3d file found in data directory")

    c3dFileAdapter.setLocationForForceExpression(
        osim.C3DFileAdapter.ForceLocation_CenterOfPressure
    )
    dynamic_tables = c3dFileAdapter.read(dynamic_c3d_file)

    dynamic_markersTable = c3dFileAdapter.getMarkersTable(dynamic_tables)
    dynamic_markersTable = rotate_markers_z_to_y(dynamic_markersTable)
    dynamic_markersTable = filter_markers(dynamic_markersTable)
    trcFileAdapter.write(dynamic_markersTable, os.path.join(outputs_path, "dynamic_markers.trc"))

    dynamic_forcesTable = c3dFileAdapter.getForcesTable(dynamic_tables)
    dynamic_forcesTable = rotate_forces_z_to_y(dynamic_forcesTable)
    dynamic_forcesTable = zero_unloaded_plates(dynamic_forcesTable, threshold=20.0)
    dynamic_forcesTable = filter_forces(dynamic_forcesTable, cutoff_hz=10.0)
    return dynamic_forcesTable
