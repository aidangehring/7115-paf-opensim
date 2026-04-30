import os
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
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
    ncols = 2
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(12, 4 * nrows))
    axes = np.array(axes).flatten()

    for idx, (r_col, l_col, title) in enumerate(pairs):
        ax = axes[idx]
        t = df["time"]
        if r_col in df.columns:
            ax.plot(t, df[r_col], color="#e74c3c", label="Right", linewidth=1.5)
        if l_col in df.columns:
            ax.plot(t, df[l_col], color="#3498db", label="Left",  linewidth=1.5, linestyle="--")
        ax.set_title(title, fontweight="bold")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel(ylabel)
        ax.axhline(0, color="k", linewidth=0.5, alpha=0.4)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)

    for idx in range(n, len(axes)):
        axes[idx].set_visible(False)

    plt.tight_layout()
    return fig


tab_hip, tab_knee, tab_ankle = st.tabs(["Hip", "Knee", "Ankle / Foot"])

with tab_hip:
    pairs = [
        ("hip_flexion_r_moment",   "hip_flexion_l_moment",   f"Hip Flexion Moment ({moment_unit})"),
        ("hip_adduction_r_moment", "hip_adduction_l_moment", f"Hip Adduction Moment ({moment_unit})"),
        ("hip_rotation_r_moment",  "hip_rotation_l_moment",  f"Hip Rotation Moment ({moment_unit})"),
    ]
    pairs = [(r, l, t) for r, l, t in pairs if r in df.columns or l in df.columns]
    if pairs:
        st.pyplot(bilateral_fig(df, pairs, f"Moment ({moment_unit})"))
    else:
        st.info("No hip moment columns found in ID output.")

with tab_knee:
    pairs = [
        ("knee_angle_r_moment", "knee_angle_l_moment", f"Knee Flexion Moment ({moment_unit})"),
    ]
    pairs = [(r, l, t) for r, l, t in pairs if r in df.columns or l in df.columns]
    if pairs:
        st.pyplot(bilateral_fig(df, pairs, f"Moment ({moment_unit})"))
    else:
        st.info("No knee moment columns found in ID output.")

with tab_ankle:
    pairs = [
        ("ankle_angle_r_moment",    "ankle_angle_l_moment",    f"Ankle Moment ({moment_unit})"),
        ("subtalar_angle_r_moment", "subtalar_angle_l_moment", f"Subtalar Moment ({moment_unit})"),
        ("mtp_angle_r_moment",      "mtp_angle_l_moment",      f"MTP Moment ({moment_unit})"),
    ]
    pairs = [(r, l, t) for r, l, t in pairs if r in df.columns or l in df.columns]
    if pairs:
        st.pyplot(bilateral_fig(df, pairs, f"Moment ({moment_unit})"))
    else:
        st.info("No ankle/foot moment columns found in ID output.")
