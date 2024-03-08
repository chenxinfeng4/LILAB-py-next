#%%
import cv2
import os
import os.path as osp
import ffmpegcv
import matplotlib.pyplot as plt

k=6
vfile = f'/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-1-30_sync/2024-01-30_18-00-01_cam{k}.mkv'

#%%
vid = ffmpegcv.VideoCaptureNV(vfile, 
                crop_xywh=[130*4,0,210*4-130*4,80])

ret,frame = vid.read()

plt.imshow(frame)
#%%
import datetime
t_start = datetime.datetime(2024,1,30, 18, 00, 4)
deltea = datetime.timedelta(seconds=1)

outdir = '/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-1-30_sync/timeocr'
os.makedirs(outdir, exist_ok=True)
outfile_prefix = osp.join(outdir, f'cam{k}')

for _ in range(1, 25*k):
    ret,frame = vid.read()
t_start = t_start + deltea*k

while True:
    out_jpg =  outfile_prefix + t_start.strftime('%Y-%m-%d_%H-%M-%S') + '.jpg'
    cv2.imwrite(out_jpg, frame)
    for _ in range(25*6):
        ret,frame = vid.read()
        if not ret: break
    if not ret: break
    t_start = t_start + deltea*6

# %%
