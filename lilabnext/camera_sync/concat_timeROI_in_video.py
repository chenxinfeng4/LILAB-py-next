#%% python -m lilabnext.camera_sync.predict_time_in_video xxx.mp4 
import os.path as osp
import ffmpegcv
import numpy as np
import tqdm
from lilab.cameras_setup import get_view_xywh_wrapper
import multiprocessing as mp
import argparse


vfile = '/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-1-31_sync/ledon/2024-01-31_13-42-57.mp4'

#%%
def concat_video_timeROI_low(vfile:str, setupname:str):
    vid = ffmpegcv.VideoCapture(vfile)
    crop_xywh_l = get_view_xywh_wrapper(setupname)
    vfile_roi = osp.splitext(vfile)[0]+'_timeROI.mp4'
    vid_out = ffmpegcv.VideoWriter(vfile_roi, None, vid.fps)

    for frame in tqdm.tqdm(vid):
        frame_roi_l = []
        for x,y,w,h in crop_xywh_l:
            frame_roi_l.append(frame[y:y+20, x+130:x+210])
        mat = np.concatenate(frame_roi_l, axis=0)
        vid_out.write(mat)
    vid.release()
    vid_out.release()


def concat_video_timeROI_high(vfile:str, setupname:str):
    npannel = len(get_view_xywh_wrapper(setupname))
    vfilemkv_l = [vfile.replace('.mp4', f'_cam{i+1}.mkv') for i in range(npannel)]
    vfile_roi_hdq = osp.splitext(vfile)[0]+'_timeROI_hdq.mp4'
    assert all(osp.isfile(f) for f in vfilemkv_l)
    vidmkv_l = [ffmpegcv.VideoCaptureNV(vfile, crop_xywh=[130*4,0,210*4-130*4,80]) for vfile in vfilemkv_l]
    vid_out = ffmpegcv.VideoWriter(vfile_roi_hdq, None, vidmkv_l[0].fps)
    counts = min(len(v) for v in vidmkv_l)
    for frames in tqdm.tqdm(zip(*vidmkv_l), total=counts, position=1):
        mat = np.concatenate(frames, axis=0)
        vid_out.write(mat)
    vid_out.release()
    for v in vidmkv_l: v.release()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('vfile', type=str, help='video file')
    parser.add_argument('--setupname', type=str, default='frank', help='setup name')
    args = parser.parse_args()

    p1 = mp.Process(target=concat_video_timeROI_low,  args=(args.vfile, args.setupname))
    p2 = mp.Process(target=concat_video_timeROI_high, args=(args.vfile, args.setupname))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    
# 
"""
low = [5,6,[1,2,3,4]]
high = [5,[2,3],1,[4,6]]
jit_in_low = [0,0,0,0,1,1]

"""