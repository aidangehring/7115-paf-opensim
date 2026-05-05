import os
import streamlit as st
from utils.config import id_path
from utils.helpers import load_mot, bilateral_fig

st.title("Inverse Dynamics")

#*-- Set to empty until the pipeline is run ------------------------------
@st.cache_data
def get_id_data():
    return load_mot(id_path)


if "id_cache_cleared" not in st.session_state:
    get_id_data.clear()
    st.session_state["id_cache_cleared"] = True

if not st.session_state.get("pipeline_complete", False):
    st.info("Run the pipeline on the Overview page to see results.")
    st.stop()

if not os.path.exists(id_path):
    st.warning("ID output file not found. Re-run the pipeline.")
    st.stop()
#*------- get id outputs into a dataframe ----------------
df = get_id_data()

#*------- get body mass from static weight extraction to normalize ID values ------------
body_mass = st.session_state.get("subject_mass")
if body_mass:
    moment_cols = [c for c in df.columns if c != "time"]
    df = df.copy()
    df[moment_cols] = df[moment_cols] / body_mass
    moment_unit = "Nm/kg"
else:
    moment_unit = "Nm"

#* --------------- Init selection tabs ----------------------------
tab_hip, tab_knee, tab_ankle = st.tabs(
    ["Hip", "Knee", "Ankle"]
)

#* ------------- Define plot outputs for each tab ----------------------------------------
with tab_hip:
    pairs = [(r, l, t) for r, l, t in [
        ("hip_flexion_r_moment",   "hip_flexion_l_moment",   f"Hip Flexion Moment ({moment_unit}) (Flex+)"),
        ("hip_adduction_r_moment", "hip_adduction_l_moment", f"Hip Adduction Moment ({moment_unit}) (Add+)"),
        ("hip_rotation_r_moment",  "hip_rotation_l_moment",  f"Hip Rotation Moment ({moment_unit})(In+)"),
    ] if r in df.columns or l in df.columns]
    if pairs:
        st.plotly_chart(bilateral_fig(df, pairs, f"Moment ({moment_unit})"), width="stretch")
    else:
        st.info("No hip moment columns found in ID output.")

with tab_knee:
    pairs = [(r, l, t) for r, l, t in [
        ("knee_angle_r_moment", "knee_angle_l_moment", f"Knee Flexion Moment ({moment_unit}) (Flex+)"),
    ] if r in df.columns or l in df.columns]
    if pairs:
        st.plotly_chart(bilateral_fig(df, pairs, f"Moment ({moment_unit})"), width="stretch")
    else:
        st.info("No knee moment columns found in ID output.")

with tab_ankle:
    pairs = [(r, l, t) for r, l, t in [
        ("ankle_angle_r_moment",    "ankle_angle_l_moment",    f"Ankle Moment ({moment_unit}) (Dorsi+)"),
    ] if r in df.columns or l in df.columns]
    if pairs:
        st.plotly_chart(bilateral_fig(df, pairs, f"Moment ({moment_unit})"), width="stretch")
    else:
        st.info("No ankle/foot moment columns found in ID output.")


