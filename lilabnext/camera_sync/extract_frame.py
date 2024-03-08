import cv2
import os
import os.path as osp
import ffmpegcv
import matplotlib.pyplot as plt
import numpy as np
vfile = '/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-1-30_sync/2024-01-30_13-38-05.mp4'

#%%
vid = ffmpegcv.VideoCaptureNV(vfile)
ret,frame = vid.read()

H,W = frame.shape[0]//2, frame.shape[1]//3
crop_xywh_f = [[0,0,W,H], [W,0,W,H], [2*W,0,W,H],[0,H,W,H], [W,H,W,H], [2*W,H,W,H]]

m=np.concatenate([frame[:20, 130:210],
                frame[:20, W+130:W+210],
                frame[:20, 2*W+130:2*W+210],
                frame[H:H+20, 130:210],
                frame[H:H+20, W+130:W+210],
                frame[H:H+20, 2*W+130:2*W+210]],
                axis=0)
plt.imshow(m)
#%%
import itertools
import datetime
t_start = datetime.datetime(2024, 1, 30, 13, 38, 5)
deltea = datetime.timedelta(seconds=1)

outdir = '/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-1-30_sync/timeocr_thumb'
os.makedirs(outdir, exist_ok=True)
outfile_prefix = osp.join(outdir, 'thumb')
for ipannel, (x,y,w,h) in itertools.cycle(enumerate(crop_xywh_f)):
    frame_crop = frame[y:y+h, x:x+w]
    frame_crop_time = frame_crop[:20, 130:210]
    out_jpg =  outfile_prefix + t_start.strftime('%Y-%m-%d_%H-%M-%S') + '.jpg'
    cv2.imwrite(out_jpg, frame_crop_time)
    for _ in range(25):
        ret,frame = vid.read()
        if not ret: break
    if not ret: break
    t_start = t_start + deltea

# %%
