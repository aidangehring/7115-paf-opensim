import opensim as osim
import pandas as pd


def rotate_markers_z_to_y(markersTable):
    for i in range(markersTable.getNumRows()):
        row = markersTable.getRowAtIndex(i)
        for j in range(row.size()):
            vec = row[j]
            x, y, z = vec[0], vec[1], vec[2]
            row[j] = osim.Vec3(x, z, -y)
        markersTable.setRowAtIndex(i, row)
    return markersTable


def load_mot(file_path) -> pd.DataFrame:
    with open(file_path, 'r') as f:
        lines = f.readlines()
    start_idx = next(
        (i + 1 for i, line in enumerate(lines) if "endheader" in line.lower()),
        1
    )
    return pd.read_csv(file_path, sep='\t', skiprows=start_idx, header=0)
