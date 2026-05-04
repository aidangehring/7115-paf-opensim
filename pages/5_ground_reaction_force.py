import os
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.config import forces_path
from utils.helpers import load_mot

st.title("Ground Reaction Forces")

st.write( "The plots below display the magnitude of the ground reaction force data\
         for the plates in the rubber and landing area. The values are normalized to\
         bodyweight.")

#* ---- Set to empty until pipeline is run ----------------------
@st.cache_data
def get_forces():
    return load_mot(forces_path)

if "grf_cache_cleared" not in st.session_state:
    get_forces.clear()
    st.session_state["grf_cache_cleared"] = True

if not st.session_state.get("pipeline_complete", False):
    st.info("Run the pipeline on the Overview page to see results.")
    st.stop()

if not os.path.exists(forces_path):
    st.warning("Forces file not found. Re-run the pipeline.")
    st.stop()

#* ---- Get prereq data --------------------------
df   = get_forces()
t    = df["time"].values

body_mass  = st.session_state.get("subject_mass")
bw         = body_mass * 9.81 if body_mass else None
force_unit = "N/BW" if bw else "N"

#* ----- Define which plate is which -----------------------
PLATES = {2: "Rubber", 3: "Landing"}

COMPONENTS = {
    "_1": ("In line with target  (+ve = pushing towards home plate)", "#27ae60"),
    "_2": ("Vertical  (+ve = force applied into the ground)",         "#2980b9"),
}


#* ---------  Create Ground reaction force data using only Vertical and shear GRF --------
def plate_fig(plate_num):
    fig = make_subplots(rows=2, cols=1,
                        subplot_titles=[COMPONENTS[s][0] for s in COMPONENTS],
                        shared_xaxes=True, vertical_spacing=0.25)

    for row_idx, (suffix, (label, color)) in enumerate(COMPONENTS.items(), start=1):
        y = df[f"f{plate_num}{suffix}"].values
        fig.add_trace(
            go.Scatter(x=t, y=y / bw if bw else y, name=label,
                       line=dict(color=color, width=1.5)),
            row=row_idx, col=1,
        )
        fig.add_hline(y=0, line=dict(color="black", width=0.5), opacity=0.35,
                      row=row_idx, col=1)
        fig.update_yaxes(title_text=force_unit, row=row_idx, col=1)

    fig.update_xaxes(title_text="Time (s)", row=2, col=1)
    fig.update_layout(height=560, template="plotly_white")
    return fig


#* ---- init control over which plate to view -----------
for tab, (n, name) in zip(st.tabs(list(PLATES.values())), PLATES.items()):
    with tab:
        fig = plate_fig(n)
        if fig:
            st.plotly_chart(fig, width="stretch")
        else:
            st.info(f"No force data for {name} plate.")
