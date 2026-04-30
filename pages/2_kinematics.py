import os
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
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


def bilateral_fig(df, pairs, ylabel):
    """pairs: list of (right_col, left_col, title)"""
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


tab_le, tab_pelvis, tab_lumbar = st.tabs(["Lower Extremity", "Pelvis", "Lumbar"])

with tab_le:
    pairs = [
        ("hip_flexion_r",    "hip_flexion_l",    "Hip Flexion / Extension (°)"),
        ("hip_adduction_r",  "hip_adduction_l",  "Hip Adduction / Abduction (°)"),
        ("knee_angle_r",     "knee_angle_l",     "Knee Flexion / Extension (°)"),
        ("ankle_angle_r",    "ankle_angle_l",    "Ankle Dorsi / Plantarflexion (°)"),
        ("subtalar_angle_r", "subtalar_angle_l", "Subtalar Inversion / Eversion (°)"),
        ("mtp_angle_r",      "mtp_angle_l",      "MTP Angle (°)"),
    ]
    pairs = [(r, l, t) for r, l, t in pairs if r in df.columns or l in df.columns]
    st.pyplot(bilateral_fig(df, pairs, "Angle (°)"))

with tab_pelvis:
    cols_pelvis = [
        ("pelvis_tilt",     "Pelvis Tilt (°)"),
        ("pelvis_list",     "Pelvis List (°)"),
        ("pelvis_rotation", "Pelvis Rotation (°)"),
    ]
    available = [(c, t) for c, t in cols_pelvis if c in df.columns]
    if available:
        fig, axes = plt.subplots(1, len(available), figsize=(5 * len(available), 4))
        axes = np.array(axes).flatten()
        for ax, (col, title) in zip(axes, available):
            ax.plot(df["time"], df[col], color="#2ecc71", linewidth=1.5)
            ax.set_title(title, fontweight="bold")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Angle (°)")
            ax.axhline(0, color="k", linewidth=0.5, alpha=0.4)
            ax.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("No pelvis columns found in IK output.")

with tab_lumbar:
    cols_lumbar = [
        ("lumbar_extension", "Lumbar Extension (°)"),
        ("lumbar_bending",   "Lumbar Bending (°)"),
        ("lumbar_rotation",  "Lumbar Rotation (°)"),
    ]
    available = [(c, t) for c, t in cols_lumbar if c in df.columns]
    if available:
        fig, axes = plt.subplots(1, len(available), figsize=(5 * len(available), 4))
        axes = np.array(axes).flatten()
        for ax, (col, title) in zip(axes, available):
            ax.plot(df["time"], df[col], color="#9b59b6", linewidth=1.5)
            ax.set_title(title, fontweight="bold")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Angle (°)")
            ax.axhline(0, color="k", linewidth=0.5, alpha=0.4)
            ax.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("No lumbar columns found in IK output.")
