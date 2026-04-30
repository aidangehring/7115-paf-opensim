import os
import streamlit as st
from utils.config import data_path, outputs_path
from utils.data_loader import load_static, load_dynamic
from utils.pipeline import run_scale, run_ik, run_id

st.title("Biomechanics Analysis Pipeline")
st.caption("Upload your C3D files, then run the OpenSim pipeline.")

# ── File upload ───────────────────────────────────────────────────────────────
st.subheader("1. Upload C3D Files")
col_static, col_dynamic = st.columns(2)

with col_static:
    static_upload = st.file_uploader("Static trial", type="c3d", key="static_c3d")
    if static_upload:
        dest = os.path.join(data_path, "static.c3d")
        with open(dest, "wb") as f:
            f.write(static_upload.getbuffer())
        st.session_state["static_ready"] = True
        st.success(f"Saved → {dest}")

with col_dynamic:
    dynamic_upload = st.file_uploader("Dynamic trial", type="c3d", key="dynamic_c3d")
    if dynamic_upload:
        dest = os.path.join(data_path, "movement.c3d")
        with open(dest, "wb") as f:
            f.write(dynamic_upload.getbuffer())
        st.session_state["dynamic_ready"] = True
        st.success(f"Saved → {dest}")

# Ready only if uploaded this session — resets on refresh
static_ready  = st.session_state.get("static_ready",  False)
dynamic_ready = st.session_state.get("dynamic_ready", False)

c1, c2 = st.columns(2)
c1.metric("Static C3D",  "✓ Ready" if static_ready  else "Not uploaded")
c2.metric("Dynamic C3D", "✓ Ready" if dynamic_ready else "Not uploaded")

st.divider()



# ── Run pipeline ──────────────────────────────────────────────────────────────
st.subheader("2. Run")
if not (static_ready and dynamic_ready):
    st.info("Upload both C3D files above before running the pipeline.")
else:
    if st.button("▶  Run Full Pipeline", type="primary"):
        try:
            with st.status("Running pipeline…", expanded=True) as status:
                st.write("⏳ Loading static trial…")
                mass, t_start, t_end = load_static()
                st.session_state["subject_mass"] = abs(mass)
                st.write(f"✅ Static loaded — subject mass: **{abs(mass):.1f} kg**")

                st.write("⏳ Loading dynamic trial…")
                dynamic_forcesTable = load_dynamic()
                st.write("✅ Dynamic trial loaded.")

                st.write("⏳ Scaling model…")
                run_scale(mass, t_start, t_end)
                st.write("✅ Model scaled and markers placed.")

                st.write("⏳ Running inverse kinematics…")
                run_ik()
                st.write("✅ Inverse kinematics complete.")

                st.write("⏳ Running inverse dynamics…")
                run_id(dynamic_forcesTable)
                st.write("✅ Inverse dynamics complete.")

                status.update(label="Pipeline complete!", state="complete")

            st.session_state["pipeline_complete"] = True
            st.success("Navigate to Kinematics or Kinetics in the sidebar to view results.")

        except Exception as e:
            st.error(f"Pipeline failed: {e}")


