#%%
import pickle
import numpy as np
from multiview_calib.calibpkl_predict import CalibPredict
from lilabnext.multiview_marmoset_yolo_track.kalmanFilter import kalmanFilter
import os.path as osp
import argparse

pklfile = '/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-1-31_sync/ballmove/2024-01-31_13-47-48.mkv.matcalibpkl'

def main(pklfile):
    with open(pklfile, 'rb') as f:
        pkldata = pickle.load(f)
    calibpredict = CalibPredict(pkldata)
    calibpredict.image_shape = None

    keypoints_xyz_ba = pkldata['keypoints_xyz_ba']
    p3d_kalman = np.zeros_like(keypoints_xyz_ba)
    for ikpt in range(keypoints_xyz_ba.shape[1]):
        forward = kalmanFilter(keypoints_xyz_ba[:,ikpt], q_=0.01, r_=1)
        backward = kalmanFilter(keypoints_xyz_ba[::-1,ikpt], q_=0.01, r_=1)[::-1]
        p3d_kalman[:,ikpt] = (forward+backward)/2

    keypoints_xyz_ba[np.isnan(keypoints_xyz_ba)] = p3d_kalman[np.isnan(keypoints_xyz_ba)]
    p2d_kalman = calibpredict.p3d_to_p2d(p3d_kalman)

    ROI_WH = (256,256)
    ORI_WH = pkldata['ba_poses'][0]['image_shape'][::-1]

    ROI_WH = np.array(ROI_WH)
    ORI_WH = np.array(ORI_WH)
    xy =  np.clip(p2d_kalman//2*2, ROI_WH/2, ORI_WH - ROI_WH/2 - 2).astype(int)
    roi_tracking_xy = xy - ROI_WH//2
    pkldata['keypoints_xyz_kalman'] = p3d_kalman
    pkldata['roi_tracking_xy'] = roi_tracking_xy
    pkldata['roi_wh'] = ROI_WH

    with open(pklfile, 'wb') as f:
        pickle.dump(pkldata, f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('pklfile', type=str)
    args = parser.parse_args()
    main(args.pklfile)