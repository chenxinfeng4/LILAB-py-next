#%%
import ffmpegcv
import numpy as np
import argparse
import pickle
import tqdm
import os.path as osp
from lilabnext.camera_sync.mkv_videos_reader import get_mkv_reader

vfile='/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-1-31_sync/ballmove/2024-01-31_13-47-48.mp4'
pklfile='/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-1-31_sync/ballmove/2024-01-31_13-47-48.mkv.matcalibpkl'
# %%
def crop_nv12_image(frame_nv12:np.ndarray, crop_xywh:np.ndarray):
    assert np.all(crop_xywh % 2 == 0)
    H,W = frame_nv12.shape[0]//3*2, frame_nv12.shape[1]
    crop_xyxy = crop_xywh + [0,0,*crop_xywh[:2]]
    assert np.all(crop_xyxy>=0) and np.all(crop_xyxy<[W,H,W,H])
    x,y,x2,y2 = crop_xyxy
    Y_crop=frame_nv12[y:y2,x:x2]
    UV_crop = frame_nv12[H:][y//2:y2//2,x:x2]
    frame_NV12_crop = np.concatenate([Y_crop,UV_crop],axis=0)
    return frame_NV12_crop


vid = get_mkv_reader(vfile, pix_fmt='nv12')
pkldata = pickle.load(open(pklfile,'rb'))
roi_tracking_xy = pkldata['roi_tracking_xy'] #nview, nsample, nkpt, 2
roi_wh = pkldata['roi_wh']
nview = len(roi_tracking_xy)
nkpt = roi_tracking_xy.shape[2]
roi_tracking_xywh = np.concatenate([roi_tracking_xy, 
                                    np.zeros_like(roi_tracking_xy)+roi_wh[None,None,None,:]], 
                                    axis=-1)
outfiles = [osp.splitext(vfile)[0]+f'_cam{i+1}_trackROI.mp4' for i in range(nview)]
outvids = [ffmpegcv.VideoWriter(f, fps=vid.fps, pix_fmt='nv12') for f in outfiles]

for i, frames in enumerate(tqdm.tqdm(vid)):
    for iview in range(nview):
        frame_nv12 = frames[iview]
        out_frame = []
        for ikpt in range(nkpt):
            crop_xywh = roi_tracking_xywh[iview,i,ikpt]
            frame_NV12_crop = crop_nv12_image(frame_nv12, crop_xywh)
            out_frame.append(frame_NV12_crop)
        out_frame = np.concatenate(out_frame, axis=1)
        outvids[iview].write(out_frame)

vid.release()
for v in outvids:
    v.release()
