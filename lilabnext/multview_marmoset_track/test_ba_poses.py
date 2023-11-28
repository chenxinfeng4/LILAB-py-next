#%%
import pickle
import numpy as np

pklfile='/mnt/liying.cibr.ac.cn_Data_Temp/multiview_9/chenxf/ana/2023-10-23/BALL_2023-10-24_12-25-19.calibpkl'
pkldata=pickle.load(open(pklfile,'rb'))
pkldata2=pickle.load(open(pklfile,'rb'))
ba_poses = pkldata['ba_poses']
for k, v in ba_poses.items():
    for vk, vv in v.items():
        ba_poses[k][vk] = np.array(vv, dtype=float)

    v['dist']*=0

# %%
from multiview_calib.calibpkl_predict import CalibPredict
calibPred = CalibPredict({'ba_poses':ba_poses})
calibPred2 = CalibPredict({'ba_poses':pkldata2['ba_poses']})
# %%
p2d_0 = calibPred2.p3d_to_p2d(np.array([0,0,0], dtype=float))
p2d_1 = calibPred.p3d_to_p2d(np.array([0,0,0], dtype=float))

X = np.array([0, 0, 0, 1.0])
K, R, t = ba_poses[0]['K'], ba_poses[0]['R'], ba_poses[0]['t']
P = np.dot(np.hstack((R, t.reshape(-1, 1))), X)
x = P[0] / P[2]
y = P[1] / P[2]
u = K[0, 0] * x + K[0, 2]
v = K[1, 1] * y + K[1, 2]
# 输出像素坐标位置
print("投影位置（u，v）：", u, v)


def get_cam_pos(R,t):
    cam_pos = (- np.linalg.inv(R) @ t.reshape(-1, 1)).ravel()
    return cam_pos

nview = max(ba_poses.keys())+1
cam_pos = np.zeros((nview, 3))
for i in range(nview):
    R, t = ba_poses[i]['R'], ba_poses[i]['t']
    cam_pos[i] = get_cam_pos(R,t)

X = np.array([ * (- np.linalg.inv(R) @ t.reshape(-1, 1)).ravel(), 1.0])
P = np.dot(np.hstack((R, t.reshape(-1, 1))), X)




t_l_2d = calibPred2.p3d_to_p2d(cam_pos, image_shape=np.array([800, 1280]))

#%%
import matplotlib.pyplot as plt
plt.figure()
iview=8
img=plt.imread(f'/mnt/liying.cibr.ac.cn_Data_Temp/multiview_9/chenxf/ana/2023-10-23/BALL_2023-10-24_12-25-19-label-{iview}.jpg')
plt.imshow(img)

plt.scatter(t_l_2d[iview][:,0], t_l_2d[iview][:,1], 50)
#%%
import copy
def move_axis_oringe(ba_poses, dxyz):
    ba_poses = copy.deepcopy(ba_poses)
    dxyz = np.array(dxyz).reshape(-1, 1)
    for i in range(len(ba_poses)):
        ba_poses[i]['t'] += (ba_poses[i]['R']@dxyz).ravel()
    return ba_poses

r_inv = np.linalg.inv(ba_poses[0]['R'])
def rotate_axis_oringe(ba_poses, r_inv):
    ba_poses = copy.deepcopy(ba_poses)
    for i in range(len(ba_poses)):
        ba_poses[i]['R'] = ba_poses[i]['R']@r_inv
    return ba_poses

ba_poses3 = move_axis_oringe(ba_poses, cam_pos[0])
ba_poses3 = rotate_axis_oringe(ba_poses3, r_inv)
cam_pos3 = np.zeros((nview, 3))
for i in range(nview):
    R, t = ba_poses3[i]['R'], ba_poses3[i]['t']
    cam_pos3[i] = get_cam_pos(R,t)
cam_pos3 = np.round(cam_pos3, 1)
cam_pos_ = np.round(cam_pos - cam_pos[[0]])
cam_pos3 - cam_pos_
t_l_2d_3 = CalibPredict({'ba_poses':ba_poses3}).p3d_to_p2d(cam_pos3)
t_l_2d = CalibPredict({'ba_poses':ba_poses}).p3d_to_p2d(cam_pos)
np.round(t_l_2d_3[3] - t_l_2d[3], 1)


CalibPredict({'ba_poses':ba_poses3}).p3d_to_p2d(np.array([10,0, 10]))[0]
calibPred = CalibPredict({'ba_poses':ba_poses})
calibPred.p3d_to_p2d(np.array([0,0,0], dtype=np.int32))
p3d_0 = calibPred2.p2d_to_p3d(p2d_0)

p3d_1 = calibPred.p2d_to_p3d(p2d_0)
pkldata2['ba_poses'][1]['t']

# %%
