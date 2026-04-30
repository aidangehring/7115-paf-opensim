import os
import opensim as osim
from utils.config import assets_path, outputs_path, stoFileAdapter, osimModel, scaleTool


def run_scale(mass, t_start, t_end):
    timeRange = osim.ArrayDouble()
    timeRange.set(0, t_start)
    timeRange.set(1, t_end)

    scaled_model_path        = os.path.join(outputs_path, "scaled_model.osim")
    scaled_model_placed_path = os.path.join(outputs_path, "scaled_model_placed.osim")
    static_trc_path          = os.path.join(outputs_path, "static_markers.trc")

    scaleTool.setSubjectMass(abs(mass))
    scaleTool.getGenericModelMaker().setModelFileName(os.path.join(assets_path, "testing.osim"))

    modelScaler = scaleTool.getModelScaler()
    modelScaler.setApply(True)
    modelScaler.setMarkerFileName(static_trc_path)
    modelScaler.setTimeRange(timeRange)
    modelScaler.setPreserveMassDist(True)
    modelScaler.setOutputModelFileName(scaled_model_path)
    modelScaler.processModel(osimModel, "", abs(mass))

    scaled_model = osim.Model(scaled_model_path)
    markerPlacer = scaleTool.getMarkerPlacer()
    markerPlacer.setApply(True)
    markerPlacer.setStaticPoseFileName(static_trc_path)
    markerPlacer.setTimeRange(timeRange)
    markerPlacer.setOutputModelFileName(scaled_model_placed_path)
    markerPlacer.setMaxMarkerMovement(-1)
    markerPlacer.processModel(scaled_model)
    scaled_model.printToXML(scaled_model_path)


def run_ik():
    model = osim.Model(os.path.join(outputs_path, "scaled_model_placed.osim"))
    ikTool = osim.InverseKinematicsTool()
    ikTool.setModel(model)
    ikTool.setMarkerDataFileName(os.path.join(outputs_path, "dynamic_markers.trc"))
    ikTool.setOutputMotionFileName(os.path.join(outputs_path, "ik_motion.mot"))
    ikTool.run()


def run_id(dynamic_forcesTable):
    stoFileAdapter.write(
        dynamic_forcesTable.flatten(),
        os.path.join(outputs_path, "forces.sto")
    )

    forces_sto_path    = os.path.abspath(os.path.join(outputs_path, "forces.sto"))
    ik_mot_path        = os.path.abspath(os.path.join(outputs_path, "ik_motion.mot"))
    ext_loads_xml_path = os.path.abspath(os.path.join(assets_path, "externalLoads.xml"))

    id_model = osim.Model(os.path.join(outputs_path, "scaled_model_placed.osim"))
    id_tool  = osim.InverseDynamicsTool(os.path.abspath(os.path.join(assets_path, "IDSettings.xml")))
    id_tool.setModel(id_model)
    id_tool.setCoordinatesFileName(ik_mot_path)

    ext_loads = osim.ExternalLoads(ext_loads_xml_path, True)
    ext_loads.setDataFileName(forces_sto_path)

    temp_xml = os.path.abspath("temp_ext_loads.xml")
    ext_loads.printToXML(temp_xml)
    id_tool.setExternalLoadsFileName(temp_xml)
    id_tool.run()
    os.remove(temp_xml)
