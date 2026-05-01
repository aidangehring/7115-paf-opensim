import os
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.config import outputs_path
from utils.helpers import load_mot

IK_PATH = os.path.join(outputs_path, "ik_motion.mot")

st.title("Inverse Kinematics")

@st.cache_data
def get_ik_data():
    return load_mot(IK_PATH)

# Clear stale cache on every new session so fresh pipeline output is always loaded
if "ik_cache_cleared" not in st.session_state:
    get_ik_data.clear()
    st.session_state["ik_cache_cleared"] = True

if not st.session_state.get("pipeline_complete", False):
    st.info("Run the pipeline on the Overview page to see results.")
    st.stop()

if not os.path.exists(IK_PATH):
    st.warning("IK output file not found. Re-run the pipeline.")
    st.stop()


df = get_ik_data()


def angular_velocity(df):
    out = df.copy()
    t = df["time"].values
    for col in df.columns:
        if col != "time":
            out[col] = np.gradient(df[col].values, t)
    return out


def bilateral_fig(df, pairs, ylabel):
    """pairs: list of (right_col, left_col, title)"""
    n = len(pairs)
    if n == 0:
        return go.Figure()
    ncols = 2
    nrows = int(np.ceil(n / ncols))
    fig = make_subplots(rows=nrows, cols=ncols, subplot_titles=[t for _, _, t in pairs])

    t = df["time"]
    for idx, (r_col, l_col, _) in enumerate(pairs):
        row = idx // ncols + 1
        col = idx % ncols + 1
        show_legend = idx == 0
        vals = []
        if r_col in df.columns:
            fig.add_trace(go.Scatter(
                x=t, y=df[r_col],
                name="Right", line=dict(color="#e74c3c", width=1.5),
                showlegend=show_legend,
            ), row=row, col=col)
            vals.extend(df[r_col].dropna())
        if l_col in df.columns:
            fig.add_trace(go.Scatter(
                x=t, y=df[l_col],
                name="Left", line=dict(color="#3498db", width=1.5),
                showlegend=show_legend,
            ), row=row, col=col)
            vals.extend(df[l_col].dropna())
        fig.add_hline(y=0, line=dict(color="black", width=0.5), opacity=0.4, row=row, col=col)
        fig.update_xaxes(title_text="Time (s)", row=row, col=col)
        if vals:
            pad = (max(vals) - min(vals)) * 0.08 or 1.0
            y_range = [min(vals) - pad, max(vals) + pad]
        else:
            y_range = None
        fig.update_yaxes(title_text=ylabel, range=y_range, row=row, col=col)

    fig.update_layout(height=400 * nrows, template="plotly_white")
    return fig


def single_col_fig(df, cols, ylabel):
    """cols: list of (col_name, title)"""
    n = len(cols)
    if n == 0:
        return go.Figure()
    fig = make_subplots(rows=1, cols=n, subplot_titles=[t for _, t in cols])
    t = df["time"]
    for idx, (col, _) in enumerate(cols):
        vals = df[col].dropna()
        fig.add_trace(go.Scatter(
            x=t, y=df[col],
            line=dict(color="#2ecc71", width=1.5),
            showlegend=False,
        ), row=1, col=idx + 1)
        fig.add_hline(y=0, line=dict(color="black", width=0.5), opacity=0.4, row=1, col=idx + 1)
        fig.update_xaxes(title_text="Time (s)", row=1, col=idx + 1)
        if len(vals):
            pad = (vals.max() - vals.min()) * 0.08 or 1.0
            y_range = [vals.min() - pad, vals.max() + pad]
        else:
            y_range = None
        fig.update_yaxes(title_text=ylabel, range=y_range, row=1, col=idx + 1)
    fig.update_layout(height=400, template="plotly_white")
    return fig


view = st.radio("Display", ["Joint Angle", "Angular Velocity"], horizontal=True)
plot_df = angular_velocity(df) if view == "Angular Velocity" else df
ylabel = "Angular Velocity (°/s)" if view == "Angular Velocity" else "Angle (°)"

tab_pelvis, tab_hip, tab_knee, tab_ankle, tab_shoulder, tab_elbow = st.tabs(["Pelvis", "Hip", "Knee", "Ankle", "Shoulder", "Elbow"])

with tab_hip:
    pairs = [
        ("hip_flexion_r",   "hip_flexion_l",   "Hip Flexion / Extension (°)"),
        ("hip_adduction_r", "hip_adduction_l", "Hip Adduction / Abduction (°)"),
    ]
    pairs = [(r, l, t) for r, l, t in pairs if r in df.columns or l in df.columns]
    st.plotly_chart(bilateral_fig(plot_df, pairs, ylabel), width='stretch')

with tab_knee:
    pairs = [
        ("knee_angle_r", "knee_angle_l", "Knee Flexion / Extension (°)"),
    ]
    pairs = [(r, l, t) for r, l, t in pairs if r in df.columns or l in df.columns]
    st.plotly_chart(bilateral_fig(plot_df, pairs, ylabel), width='stretch')

with tab_pelvis:
    cols_pelvis = [("pelvis_tilt", "Pelvis Tilt (°)")]
    available = [(c, t) for c, t in cols_pelvis if c in df.columns]
    if available:
        st.plotly_chart(single_col_fig(plot_df, available, ylabel), width='stretch')
    else:
        st.info("No pelvis columns found in IK output.")

with tab_ankle:
    pairs = [
        ("ankle_angle_r", "ankle_angle_l", "Ankle Dorsi / Plantarflexion (°)"),
    ]
    pairs = [(r, l, t) for r, l, t in pairs if r in df.columns or l in df.columns]
    st.plotly_chart(bilateral_fig(plot_df, pairs, ylabel), width='stretch')

with tab_shoulder:
    pairs = [
        ("arm_flex_r", "arm_flex_l", "Arm Flexion"),
        ("arm_add_r",  "arm_add_l",  "Arm Adduction"),
        ("arm_rot_r",  "arm_rot_l",  "Arm Rotation"),
    ]
    pairs = [(r, l, t) for r, l, t in pairs if r in df.columns or l in df.columns]
    st.plotly_chart(bilateral_fig(plot_df, pairs, ylabel), width='stretch')

with tab_elbow:
    pairs = [
        ("elbow_flex_r", "elbow_flex_l", "Elbow Flexion"),
    ]
    pairs = [(r, l, t) for r, l, t in pairs if r in df.columns or l in df.columns]
    st.plotly_chart(bilateral_fig(plot_df, pairs, ylabel), width='stretch')
