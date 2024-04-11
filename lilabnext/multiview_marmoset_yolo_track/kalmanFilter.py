#%%

import pickle
import numpy as np


#%%
def kalmanFilter_(trajectory, q_=0.01, r_=5):
    # q_ : 越大越平滑，(0.00, 1)
    # r_ : 越小越平滑，类似时间平移  (0.00, 1, xxx)
    Q = q_ * np.eye(3)
    R = r_ * np.eye(3)
    P = np.eye(3)
    x_hat = np.array(trajectory[0])
    filtered_trajectory = []
    for z in trajectory:
        #预测
        x_hat_minus = x_hat
        P_minus = P + Q

        #更新
        K = P_minus @ np.linalg.inv(P_minus + R)
        x_hat = x_hat_minus + K @ (z - x_hat_minus)
        P = (np.eye(3) - K) @ P_minus
        filtered_trajectory.append(x_hat)
    filtered_trajectory = np.array(filtered_trajectory)
    return filtered_trajectory

def kalmanFilter(trajectory, q_=0.01, r_=5):
    # q_ : 越大越平滑，(0.00, 1)
    # r_ : 越小越平滑，类似时间平移  (0.00, 1, xxx)
    Q = q_ * np.eye(3)
    R = r_ * np.eye(3)
    P = np.eye(3)
    x_hat = np.array(trajectory[0])
    velocity = np.zeros(3)
    filtered_trajectory = []
    for z in trajectory:
        #预测
        x_hat_minus = x_hat + velocity
        P_minus = P + Q

        #缺省时
        if np.any(np.isnan(z)):
            x_hat = x_hat_minus
        else:
            K = P_minus @ np.linalg.inv(P_minus + R)
            x_hat = x_hat_minus + K @ (z - x_hat_minus)
            velocity_minus = x_hat - x_hat_minus
            velocity_masue = z - x_hat_minus
            velocity = velocity_minus + K @ (velocity_masue - velocity_masue)
            P = (np.eye(3) - K) @ P_minus
        filtered_trajectory.append(x_hat)
    filtered_trajectory = np.array(filtered_trajectory)
    return filtered_trajectory
#%%



#%%
def kalmanFilterRT(q_=0.01, r_=5):
    Q = q_ * np.eye(3)
    R = r_ * np.eye(3)
    P = np.eye(3)
    x_hat = None

    def func(z):
        nonlocal P, x_hat
        if x_hat is None: x_hat = np.array(z)
        #预测
        x_hat_minus = x_hat
        P_minus = P + Q

        #更新
        K = P_minus @ np.linalg.inv(P_minus + R)
        x_hat = x_hat_minus + K @ (z - x_hat_minus)
        P = (np.eye(3) - K) @ P_minus
        return x_hat
    return func


def kalmanFutureRT(q_=0.01, r_=5, nfuture=5):
    Q = q_ * np.eye(3)
    R = r_ * np.eye(3)
    P = np.eye(3)
    x_hat = None
    x_hat_old = None
    velocity = np.zeros(3)

    def func(z):
        nonlocal P, x_hat, velocity, x_hat_old
        if x_hat is None: x_hat = x_hat_old = np.array(z)
        #预测
        x_hat_minus = x_hat
        P_minus = P + Q

        #更新
        K = P_minus @ np.linalg.inv(P_minus + R)
        x_hat = x_hat_minus + K @ (z - x_hat_minus)
        P = (np.eye(3) - K) @ P_minus

        #更新速度
        acceleration = x_hat + x_hat_old - 2*x_hat_minus
        velocity0 = x_hat - x_hat_minus
        x_hat_future = x_hat_minus + velocity0 * nfuture + 0.5 * acceleration * nfuture**2
        x_hat_old = x_hat_minus
        return x_hat_future
    return func



#%%
if __name__ == '__main__':
    import matplotlib.pyplot as plt
    matpklfile = '/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-1-31_sync/ballmove/ball_move.matcalibpkl'
    matpkldata = pickle.load(open(matpklfile, 'rb'))
    keypoints_xyz = matpkldata['keypoints_xyz_ba']
    trajectory = keypoints_xyz[::-1,0,:]
    filtered_trajectory = kalmanFilter_(trajectory, q_=0.005, r_=1)
    filtered_trajectory1 = kalmanFilter(trajectory, q_=0.005, r_=1)

    plt.plot(filtered_trajectory[:,1])
    plt.plot(filtered_trajectory1[:,1])
    plt.plot(trajectory[:,1], color='red')
    plt.legend(["filtered", "f2" ,"ground truth"])
    plt.xlim([1400,1700])

    kalmanFilterRTfun = kalmanFilterRT(q_=0.01, r_=1)
    filtered_trajectory = np.array([kalmanFilterRTfun(z) for z in trajectory])
    kalmanFutureRTfun = kalmanFutureRT(q_=0.01, r_=1, nfuture=20)
    future_trajectory = np.array([kalmanFutureRTfun(z) for z in trajectory])

    plt.plot(filtered_trajectory[:,1])
    # plt.plot(future_trajectory[:,1])
    plt.plot(trajectory[:,1], color='red')
    plt.legend(["filtered", "ground truth"])


    plt.xlim([2450,2700])
