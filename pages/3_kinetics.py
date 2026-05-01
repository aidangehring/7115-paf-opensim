import os
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.config import outputs_path
from utils.helpers import load_mot

ID_PATH = os.path.join(outputs_path, "inverse_dynamics.sto")

st.title("Inverse Dynamics")

@st.cache_data
def get_id_data():
    return load_mot(ID_PATH)

# Clear stale cache on every new session so fresh pipeline output is always loaded
if "id_cache_cleared" not in st.session_state:
    get_id_data.clear()
    st.session_state["id_cache_cleared"] = True

if not st.session_state.get("pipeline_complete", False):
    st.info("Run the pipeline on the Overview page to see results.")
    st.stop()

if not os.path.exists(ID_PATH):
    st.warning("ID output file not found. Re-run the pipeline.")
    st.stop()


df = get_id_data()

body_mass = st.session_state.get("subject_mass")
if body_mass:
    moment_cols = [c for c in df.columns if c != "time"]
    df = df.copy()
    df[moment_cols] = df[moment_cols] / body_mass
    moment_unit = "Nm/kg"
else:
    moment_unit = "Nm"


def bilateral_fig(df, pairs, ylabel):
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


tab_hip, tab_knee, tab_ankle, tab_shoulder, tab_elbow = st.tabs(["Hip", "Knee", "Ankle", "Shoulder", "Elbow"])

with tab_hip:
    pairs = [
        ("hip_flexion_r_moment",   "hip_flexion_l_moment",   f"Hip Flexion Moment ({moment_unit})"),
        ("hip_adduction_r_moment", "hip_adduction_l_moment", f"Hip Adduction Moment ({moment_unit})"),
        ("hip_rotation_r_moment",  "hip_rotation_l_moment",  f"Hip Rotation Moment ({moment_unit})"),
    ]
    pairs = [(r, l, t) for r, l, t in pairs if r in df.columns or l in df.columns]
    if pairs:
        st.plotly_chart(bilateral_fig(df, pairs, f"Moment ({moment_unit})"), width='stretch')
    else:
        st.info("No hip moment columns found in ID output.")

with tab_knee:
    pairs = [
        ("knee_angle_r_moment", "knee_angle_l_moment", f"Knee Flexion Moment ({moment_unit})"),
    ]
    pairs = [(r, l, t) for r, l, t in pairs if r in df.columns or l in df.columns]
    if pairs:
        st.plotly_chart(bilateral_fig(df, pairs, f"Moment ({moment_unit})"), width='stretch')
    else:
        st.info("No knee moment columns found in ID output.")

with tab_ankle:
    pairs = [
        ("ankle_angle_r_moment",    "ankle_angle_l_moment",    f"Ankle Moment ({moment_unit})"),
        ("subtalar_angle_r_moment", "subtalar_angle_l_moment", f"Subtalar Moment ({moment_unit})"),
    ]
    pairs = [(r, l, t) for r, l, t in pairs if r in df.columns or l in df.columns]
    if pairs:
        st.plotly_chart(bilateral_fig(df, pairs, f"Moment ({moment_unit})"), width='stretch')
    else:
        st.info("No ankle/foot moment columns found in ID output.")

with tab_shoulder:
    pairs = [
        ("arm_flex_r_moment", "arm_flex_l_moment", f"Arm Flexion Moment ({moment_unit})"),
        ("arm_add_r_moment",  "arm_add_l_moment",  f"Arm Adduction Moment ({moment_unit})"),
        ("arm_rot_r_moment",  "arm_rot_l_moment",  f"Arm Rotation Moment ({moment_unit})"),
    ]
    pairs = [(r, l, t) for r, l, t in pairs if r in df.columns or l in df.columns]
    if pairs:
        st.plotly_chart(bilateral_fig(df, pairs, f"Moment ({moment_unit})"), width='stretch')
    else:
        st.info("No shoulder moment columns found in ID output.")

with tab_elbow:
    pairs = [
        ("elbow_flex_r_moment", "elbow_flex_l_moment", f"Elbow Flexion Moment ({moment_unit})"),
    ]
    pairs = [(r, l, t) for r, l, t in pairs if r in df.columns or l in df.columns]
    if pairs:
        st.plotly_chart(bilateral_fig(df, pairs, f"Moment ({moment_unit})"), width='stretch')
    else:
        st.info("No elbow moment columns found in ID output.")
