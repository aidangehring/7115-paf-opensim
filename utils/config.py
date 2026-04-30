import os
import pandas as pd
import opensim as osim
import numpy as np
import matplotlib.pyplot as plt


data_path= "data"
assets_path= "assets"
outputs_path= "outputs"
c3dFileAdapter= osim.C3DFileAdapter()
trcFileAdapter= osim.TRCFileAdapter()
stoFileAdapter = osim.STOFileAdapter()
osimModel = osim.Model(os.path.join(assets_path, "testing.osim"))
scaleTool = osim.ScaleTool(os.path.join(assets_path,"test_scale.xml"))