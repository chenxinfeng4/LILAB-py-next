#%%
import pickle
import numpy as np
from multiview_calib.calibpkl_predict import CalibPredict
import argparse

matpkl = 'ball_move_cam1.matpkl'
calibpkl = 'ball_move_cam1.calibpkl'
pod_len = 0.5


def main(matpkl, calibpkl, pod_len):
    matdata = pickle.load(open(matpkl, 'rb'))
    calibdata = pickle.load(open(calibpkl, 'rb'))
    calibPredict = CalibPredict(calibdata)
    kpt_xyp = matdata['keypoints']
    kpt_xy = kpt_xyp[..., :2]
    kpt_p = kpt_xyp[..., 2]
    ind_valid = kpt_p > 0.4
    kpt_xy[~ind_valid] = np.nan
    kpt_xyz = calibPredict.p2d_to_p3d(kpt_xy)
    pods_dist = np.linalg.norm(kpt_xyz[:,0,:] - kpt_xyz[:,1,:], axis=-1)
    pods_dist = pods_dist[~np.isnan(pods_dist)]

    pods_dist_median = np.median(pods_dist)
    pods_dist_std = np.std(pods_dist)
    scale = pod_len / pods_dist_median
    pods_dist_std_scaled = pods_dist_std * scale

    print(f'Remap double ball: mean {pod_len} +- std {pods_dist_std_scaled:.3f}')
    ba_poses = calibdata['ba_poses']
    for v in ba_poses.values():
        v['t'] *= scale
    pickle.dump(calibdata, open(calibpkl, 'wb'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('matpkl', type=str, help='path to matpkl')
    parser.add_argument('calibpkl', type=str, help='path to calibpkl')
    parser.add_argument('--pod_len', type=float, default=0.5, help='length of double ball')
    args = parser.parse_args()
    main(args.matpkl, args.calibpkl, args.pod_len)
