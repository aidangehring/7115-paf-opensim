import os
import streamlit as st
from utils.config import ik_path
from utils.helpers import load_mot, angular_velocity, find_peak_er, bilateral_fig, single_col_fig

st.title("Inverse Kinematics")

#-- Set to empty until the pipeline is run ------------------------------
@st.cache_data
def get_ik_data():
    return load_mot(ik_path)


if "ik_cache_cleared" not in st.session_state:
    get_ik_data.clear()
    st.session_state["ik_cache_cleared"] = True

if not st.session_state.get("pipeline_complete", False):
    st.info("Run the pipeline on the Overview page to see results.")
    st.stop()

if not os.path.exists(ik_path):
    st.warning("IK output file not found. Re-run the pipeline.")
    st.stop()

#------- get ik outputs into a dataframe ----------------
df   = get_ik_data()

# ------ Init interactive plot setup -----------------------------------------------
view    = st.radio("Display", ["Joint Angle", "Angular Velocity"], horizontal=True)
plot_df = angular_velocity(df) if view == "Angular Velocity" else df
ylabel  = "Angular Velocity (°/s)" if view == "Angular Velocity" else "Angle (°)"

tab_pelvis, tab_hip, tab_knee, tab_ankle, tab_shoulder, tab_elbow = st.tabs(
    ["Pelvis", "Hip", "Knee", "Ankle", "Shoulder", "Elbow"]
)
# ---------- Define output plots for each selectable tab -------------------------------------------
with tab_hip:
    pairs = [(r, l, t) for r, l, t in [
        ("hip_flexion_r",   "hip_flexion_l",   "Hip Flexion / Extension (Flex+)"),
        ("hip_adduction_r", "hip_adduction_l", "Hip Adduction / Abduction (Add+)"),
    ] if r in df.columns or l in df.columns]
    st.plotly_chart(bilateral_fig(plot_df, pairs, ylabel), width="stretch")

with tab_knee:
    pairs = [(r, l, t) for r, l, t in [
        ("knee_angle_r", "knee_angle_l", "Knee Flexion / Extension (Flex+)"),
    ] if r in df.columns or l in df.columns]
    st.plotly_chart(bilateral_fig(plot_df, pairs, ylabel), width="stretch")

with tab_pelvis:
    available = [(c, t) for c, t in [("pelvis_tilt", "Pelvis Tilt (Ant+)")] if c in df.columns]
    if available:
        st.plotly_chart(single_col_fig(plot_df, available, ylabel), width="stretch")
    else:
        st.info("No pelvis columns found in IK output.")

with tab_ankle:
    pairs = [(r, l, t) for r, l, t in [
        ("ankle_angle_r", "ankle_angle_l", "Ankle Dorsi / Plantarflexion (Dor+)"),
    ] if r in df.columns or l in df.columns]
    st.plotly_chart(bilateral_fig(plot_df, pairs, ylabel), width="stretch")

with tab_shoulder:
    pairs = [(r, l, t) for r, l, t in [
        ("arm_flex_r", "arm_flex_l", "Arm Flexion (Flex+)"),
        ("arm_add_r",  "arm_add_l",  "Arm Adduction (Add+)"),
        ("arm_rot_r",  "arm_rot_l",  "Arm Rotation (In+)"),
    ] if r in df.columns or l in df.columns]
    st.plotly_chart(bilateral_fig(plot_df, pairs, ylabel), width="stretch")

with tab_elbow:
    pairs = [(r, l, t) for r, l, t in [
        ("elbow_flex_r", "elbow_flex_l", "Elbow Flexion (Flex+)"),
    ] if r in df.columns or l in df.columns]
    st.plotly_chart(bilateral_fig(plot_df, pairs, ylabel), width="stretch")
