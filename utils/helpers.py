import numpy as np
import opensim as osim
import pandas as pd
from scipy.signal import butter, filtfilt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

_VLINE_ER = dict(color="#2c3e50", width=1.5, dash="dash")

#! --- these are all helper functions called in other areas to carry out named task ---

#* ----- rotate to opensim coordinate system -------
def rotate_markers_z_to_y(markersTable):
    for i in range(markersTable.getNumRows()):
        row = markersTable.getRowAtIndex(i)
        for j in range(row.size()):
            vec = row[j]
            x, y, z = vec[0], vec[1], vec[2]
            row[j] = osim.Vec3(x, z, -y)
        markersTable.setRowAtIndex(i, row)
    return markersTable

#* ----- rotate to opensim coordinate system -------
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

#* --- zero force plates when unloaded ------------
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

#* ---- generic lowpass butterworth filter ----------------
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

#* ---- Call butterworth filter to filter forces at specified cutoff ---------
def filter_forces(forcesTable, cutoff_hz=30.0):
    return lowpass_filter_vec3_table(forcesTable, cutoff_hz)

#* ---- Call butterworth filter to filter markers at specified cutoff ---------
def filter_markers(markersTable, cutoff_hz=10.0):
    return lowpass_filter_vec3_table(markersTable, cutoff_hz)

#* ---- create a dataframe from inverse kinematics output ------------
def load_mot(file_path) -> pd.DataFrame:
    with open(file_path, 'r') as f:
        lines = f.readlines()
    start_idx = next(
        (i + 1 for i, line in enumerate(lines) if "endheader" in line.lower()),
        1
    )
    return pd.read_csv(file_path, sep='\t', skiprows=start_idx, header=0)

#* --- Calculate angular velocity of joints via differentiation of angles -----
def angular_velocity(df):
    out = df.copy()
    t = df["time"].values
    for col in df.columns:
        if col != "time":
            out[col] = np.gradient(df[col].values, t)
    return out

#* ----- Find the instance of peak external rotation of the arm, which signifies -----
#* ----- The onset of arm acceleration -------------------
def find_peak_er(df, col="arm_rot_r"):
    if col not in df.columns:
        return None
    t = df["time"].values
    return float(t[int(np.argmin(df[col].values))])

#* ----- Template for plotting a figure which will display a bilateral joint ------
def bilateral_fig(df, pairs, ylabel, t_er=None):
    n = len(pairs)
    if n == 0:
        return go.Figure()
    nrows = int(np.ceil(n / 2))
    fig = make_subplots(rows=nrows, cols=2, subplot_titles=[title for _, _, title in pairs])
    t = df["time"]
    for idx, (r_col, l_col, _) in enumerate(pairs):
        row, col = idx // 2 + 1, idx % 2 + 1
        show_legend = idx == 0
        vals = []
        if r_col in df.columns:
            fig.add_trace(go.Scatter(x=t, y=df[r_col], name="Right",
                                     line=dict(color="#e74c3c", width=1.5),
                                     showlegend=show_legend), row=row, col=col)
            vals.extend(df[r_col].dropna())
        if l_col in df.columns:
            fig.add_trace(go.Scatter(x=t, y=df[l_col], name="Left",
                                     line=dict(color="#3498db", width=1.5),
                                     showlegend=show_legend), row=row, col=col)
            vals.extend(df[l_col].dropna())
        fig.add_hline(y=0, line=dict(color="black", width=0.5), opacity=0.4, row=row, col=col)
        fig.update_xaxes(title_text="Time (s)", row=row, col=col)
        pad = (max(vals) - min(vals)) * 0.08 or 1.0 if vals else None
        y_range = [min(vals) - pad, max(vals) + pad] if pad else None
        fig.update_yaxes(title_text=ylabel, range=y_range, row=row, col=col)
    if t_er is not None:
        fig.add_vline(x=t_er, line=_VLINE_ER, annotation_text="Peak ER",
                      annotation_position="top left")
    fig.update_layout(height=400 * nrows, template="plotly_white")
    return fig

#* --- Template to create a plot for a joint that is not bilateral --------
def single_col_fig(df, cols, ylabel, t_er=None):
    n = len(cols)
    if n == 0:
        return go.Figure()
    fig = make_subplots(rows=1, cols=n, subplot_titles=[title for _, title in cols])
    t = df["time"]
    for idx, (col, _) in enumerate(cols):
        vals = df[col].dropna()
        fig.add_trace(go.Scatter(x=t, y=df[col], line=dict(color="#2ecc71", width=1.5),
                                 showlegend=False), row=1, col=idx + 1)
        fig.add_hline(y=0, line=dict(color="black", width=0.5), opacity=0.4,
                      row=1, col=idx + 1)
        fig.update_xaxes(title_text="Time (s)", row=1, col=idx + 1)
        if len(vals):
            pad = (vals.max() - vals.min()) * 0.08 or 1.0
            fig.update_yaxes(title_text=ylabel,
                             range=[vals.min() - pad, vals.max() + pad],
                             row=1, col=idx + 1)
        else:
            fig.update_yaxes(title_text=ylabel, row=1, col=idx + 1)
    if t_er is not None:
        fig.add_vline(x=t_er, line=_VLINE_ER, annotation_text="Peak ER",
                      annotation_position="top left")
    fig.update_layout(height=400, template="plotly_white")
    return fig

#* ------ Template to create the kineamtic sequence plot with a dot on peak values---
#* ------ And a dashed line where peak external rotation of the arm occurs (arm accel)-----
def sequencing_fig(vel_df, segments, colors, title, t_er=None):
    t = vel_df["time"].values
    available = [item for item in segments if item[1] in vel_df.columns]
    if not available:
        return None, []
    fig = go.Figure()
    peaks = []
    for item in available:
        lbl, col = item[0], item[1]
        before_t = item[2] if len(item) > 2 else None
        y = vel_df[col].values
        color = colors.get(lbl, "#555555")
        if before_t is not None:
            peak_idx = int(np.argmax(np.where(t <= before_t, np.abs(y), -np.inf)))
        else:
            peak_idx = int(np.argmax(np.abs(y)))
        peak_t, peak_v = float(t[peak_idx]), float(y[peak_idx])
        peaks.append((lbl, peak_t, peak_v))
        fig.add_trace(go.Scatter(x=t, y=y, name=lbl, line=dict(color=color, width=2)))
        fig.add_trace(go.Scatter(
            x=[peak_t], y=[peak_v], mode="markers", showlegend=False,
            marker=dict(color=color, size=10, symbol="circle",
                        line=dict(color="white", width=1.5)),
            hovertemplate=f"<b>{lbl}</b><br>t = %{{x:.3f}} s<br>ω = %{{y:.1f}} °/s<extra></extra>",
        ))
        fig.add_vline(x=peak_t, line=dict(color=color, width=1, dash="dot"), opacity=0.45)
    fig.add_hline(y=0, line=dict(color="black", width=0.5), opacity=0.35)
    if t_er is not None:
        fig.add_vline(x=t_er, line=_VLINE_ER, annotation_text="Peak ER",
                      annotation_position="top left")
    fig.update_layout(
        title=dict(text=title, font=dict(size=15)),
        xaxis_title="Time (s)", yaxis_title="Angular Velocity (°/s)",
        template="plotly_white", height=480,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig, peaks
