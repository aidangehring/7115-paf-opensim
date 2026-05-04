import os
import streamlit as st

st.set_page_config(page_title='Biomechanics Report', layout='wide')

OUTPUT_FILES = [
    "outputs/static_markers.trc",
    "outputs/dynamic_markers.trc",
    "outputs/scaled_model.osim",
    "outputs/scaled_model_placed.osim",
    "outputs/ik_motion.mot",
    "outputs/forces.sto",
    "outputs/inverse_dynamics.sto",
]

if "outputs_cleared" not in st.session_state:
    for path in OUTPUT_FILES:
        if os.path.exists(path):
            os.remove(path)
    st.session_state["outputs_cleared"] = True

pg = st.navigation([
    st.Page("pages/1_Overview.py",   title="Overview"),
    st.Page("pages/2_kinematics.py", title="Kinematics"),
    st.Page("pages/3_kinetics.py",   title="Kinetics"),
    st.Page("pages/4_kinematic_sequencing.py"),
    st.Page("pages/5_ground_reaction_force.py")
])

pg.run()