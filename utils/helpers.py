import numpy as np
import opensim as osim
import pandas as pd
from scipy.signal import butter, filtfilt



def rotate_markers_z_to_y(markersTable):
    for i in range(markersTable.getNumRows()):
        row = markersTable.getRowAtIndex(i)
        for j in range(row.size()):
            vec = row[j]
            x, y, z = vec[0], vec[1], vec[2]
            row[j] = osim.Vec3(x, z, -y)
        markersTable.setRowAtIndex(i, row)
    return markersTable


def rotate_forces_z_to_y(forcesTable):
    # Forces (and COP positions, free moments) from C3D are in Z-up convention.
    # OpenSim ground frame is Y-up, so apply the same rotation as markers.
    for i in range(forcesTable.getNumRows()):
        row = forcesTable.getRowAtIndex(i)
        for j in range(row.size()):
            vec = row[j]
            row[j] = osim.Vec3(vec[0], vec[2], -vec[1])
        forcesTable.setRowAtIndex(i, row)
    return forcesTable


def zero_unloaded_plates(forcesTable, threshold=10.0):
    # Columns are grouped as [force, COP, moment] per plate (3 Vec3 cols each).
    # When vertical GRF is below threshold the COP is undefined (can be 50+ m),
    # causing enormous artificial moments in ID. Zero out the whole plate.
    n_plates = forcesTable.getNumColumns() // 3
    for i in range(forcesTable.getNumRows()):
        row = forcesTable.getRowAtIndex(i)
        changed = False
        for p in range(n_plates):
            fc = p * 3  # force column index for this plate
            if abs(row[fc][1]) < threshold:  # component 1 = Y = vertical after rotation
                row[fc]     = osim.Vec3(0, 0, 0)
                row[fc + 1] = osim.Vec3(0, 0, 0)
                row[fc + 2] = osim.Vec3(0, 0, 0)
                changed = True
        if changed:
            forcesTable.setRowAtIndex(i, row)
    return forcesTable


def lowpass_filter_vec3_table(table, cutoff_hz):
    times = list(table.getIndependentColumn())
    fs = 1.0 / (times[1] - times[0])
    b, a = butter(4, cutoff_hz / (fs / 2.0), btype='low')

    n_rows = table.getNumRows()
    n_cols = table.getNumColumns()

    data = np.zeros((n_rows, n_cols * 3))
    for i in range(n_rows):
        row = table.getRowAtIndex(i)
        for j in range(n_cols):
            vec = row[j]
            data[i, j * 3:j * 3 + 3] = [vec[0], vec[1], vec[2]]

    # filtfilt requires signal length > default padlen (3 * max(len(a), len(b))).
    # Cap padlen to half the signal length so short trials don't raise an error.
    padlen = min(3 * max(len(a), len(b)), (n_rows - 1) // 2)
    for c in range(data.shape[1]):
        data[:, c] = filtfilt(b, a, data[:, c], padlen=padlen)

    for i in range(n_rows):
        row = table.getRowAtIndex(i)
        for j in range(n_cols):
            row[j] = osim.Vec3(float(data[i, j * 3]), float(data[i, j * 3 + 1]), float(data[i, j * 3 + 2]))
        table.setRowAtIndex(i, row)

    return table


def filter_forces(forcesTable, cutoff_hz=30.0):
    return lowpass_filter_vec3_table(forcesTable, cutoff_hz)


def filter_markers(markersTable, cutoff_hz=10.0):
    return lowpass_filter_vec3_table(markersTable, cutoff_hz)




def load_mot(file_path) -> pd.DataFrame:
    with open(file_path, 'r') as f:
        lines = f.readlines()
    start_idx = next(
        (i + 1 for i, line in enumerate(lines) if "endheader" in line.lower()),
        1
    )
    return pd.read_csv(file_path, sep='\t', skiprows=start_idx, header=0)
