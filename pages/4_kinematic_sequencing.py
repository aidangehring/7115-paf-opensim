import os
import streamlit as st
import numpy as np
from utils.config import ik_path
from utils.helpers import load_mot, angular_velocity, find_peak_er, sequencing_fig

st.title("Kinematic Sequencing")

st.markdown(
    "Kinematic sequencing shows the proximal-to-distal transfer of angular velocity through\
    the kinetic chain. Peak values are represented by dots in the plot.\
    Efficient movement produces a wave pattern where each distal segment\
    peaks *after* the proximal segment has peaked and begun to decelerate.\
    Click and drag on the plot to zoom into the region of interest."
)

#* -------- set to empty until pipeline is run ----------------------------
@st.cache_data
def get_ik_data():
    return load_mot(ik_path)


if "ks_cache_cleared" not in st.session_state:
    get_ik_data.clear()
    st.session_state["ks_cache_cleared"] = True

if not st.session_state.get("pipeline_complete", False):
    st.info("Run the pipeline on the Overview page to see results.")
    st.stop()

if not os.path.exists(ik_path):
    st.warning("IK output file not found. Re-run the pipeline.")
    st.stop()

#* -------------- gather necessary preqreqs before creating kinematic sequence plot
df     = get_ik_data()
vel_df = angular_velocity(df)
t      = vel_df["time"].values
t_er   = find_peak_er(df)

#* --------- style legend ----------------
COLORS = {
    "Hip":    "#555555",
    "Pelvis": "#9b59b6",
    "Torso":  "#e74c3c",
    "Arm":    "#e67e22",
}

#* ---- define peak right arm rotation velocity so peak values are taken before this point --
#* ---- Some values like torso will have a rebound like effect where a second peak ----
#* ---- will occur, so we need to make sure the proper peak is take to represent sequence ---
arm_col    = "arm_rot_r"
arm_peak_t = float(t[int(np.argmax(np.abs(vel_df[arm_col].values)))]) if arm_col in vel_df.columns else None

#* ---- Define the segments and joint action to plot -----------
segments = [
    ("Hip",    "hip_rotation_l", arm_peak_t),
    ("Pelvis", "pelvis_rotation", arm_peak_t),
    ("Torso",  "lumbar_rotation", arm_peak_t),
    ("Arm",    arm_col),
]

#* --- Display the Hip, Pelvis, Torso (Lumbar rotation), and arm peak timings ----------
fig, peaks = sequencing_fig(vel_df, segments, COLORS, "Kinematic Sequence", t_er=t_er)
if fig:
    st.plotly_chart(fig, width="stretch")
    st.markdown("Timing of peak rotation angular velocities")
    cols = st.columns(len(peaks))
    for ui_col, (lbl, peak_t, _) in zip(cols, peaks):
        ui_col.metric(lbl, f"@ {peak_t:.3f} s")
else:
    st.info("No matching columns found in IK output.")
