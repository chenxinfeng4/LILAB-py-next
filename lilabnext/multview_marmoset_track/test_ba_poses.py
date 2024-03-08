#%%
import pickle
import numpy as np

pklfile='/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2023-11-22-calib/ball_move_cam1.calibpkl'
pkldata=pickle.load(open(pklfile,'rb'))
pkldata2=pickle.load(open(pklfile,'rb'))
ba_poses = pkldata['ba_poses']
for k, v in ba_poses.items():
    for vk, vv in v.items():
        ba_poses[k][vk] = np.array(vv, dtype=float)

# %%
from multiview_calib.calibpkl_predict import CalibPredict
calibPred = CalibPredict({'ba_poses':ba_poses})
calibPred2 = CalibPredict({'ba_poses':pkldata2['ba_poses']})
# %%
p2d = calibPred2.p3d_to_p2d(np.array([0,0,0], dtype=float))
# %%
