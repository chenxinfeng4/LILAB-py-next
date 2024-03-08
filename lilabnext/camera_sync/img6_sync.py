# %%
import ffmpegcv
import numpy as np
import os

vfile = '/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-1-31_sync/ledon/2024-01-31_13-42-57.mp4'


def get_led_value(vfile):
    vid = ffmpegcv.VideoCaptureNV(vfile,resize=(64*3, 64*2), 
                                resize_keepratio=False,
                                pix_fmt='gray')
    WH = 64
    crop_xywh = [[0,0,WH,WH], [WH,0,WH,WH], [2*WH,0,WH,WH],[0,WH,WH,WH], [WH,WH,WH,WH], [2*WH,WH,WH,WH]]

    out_np = np.zeros((len(crop_xywh), len(vid)))
    for iframe, frame in enumerate(vid):
        frame = frame.astype(np.float32)
        for i, xywh in enumerate(crop_xywh):
            frame_crop = frame[xywh[1]:xywh[1]+xywh[3], xywh[0]:xywh[0]+xywh[2]]
            out_np[i, iframe] = frame_crop.ravel().mean()


def get_led_value_deheaded(vfile):
    ncam = 6
    vfilemkv_l = [vfile.replace('.mp4', f'_cam{i+1}_dehead.mp4') for i in range(ncam)]
    # vfilemkv_l = [vfile.replace('.mp4', f'_cam{i+1}.mkv') for i in range(ncam)]
    assert all([os.path.exists(vfilemkv_l[i]) for i in range(ncam)])
    # vid_l = [ffmpegcv.VideoCaptureNV(vfile,resize=(64*2, 64*2), 
    #                             resize_keepratio=False,
    #                             pix_fmt='gray')
    #             for vfile in vfilemkv_l]
    vid_l = [ffmpegcv.VideoCaptureNV(vfile,pix_fmt='gray')
                for vfile in vfilemkv_l]
    out_np = np.zeros([ncam, min(len(vid) for vid in vid_l)])
    for iframe, frames in enumerate(zip(*vid_l)):
        for icam, frame in enumerate(frames):
            frame = frame.astype(np.float32)
            out_np[icam, iframe] = frame.mean()
    for vid in vid_l:
        vid.release()
    return out_np

# out_np = get_led_value(vfile)
out_np = get_led_value_deheaded(vfile)

# %%
import matplotlib.pyplot as plt
from lilab.comm_signal.detectTTL import detectTTL
npannel = len(out_np)
thrs = np.percentile(out_np, [20, 70], axis=-1).mean(axis=0)

thrs[5] = 110
plt.figure(figsize=(12,20))
for i in range(npannel):
    plt.subplot(npannel,1,i+1)
    plt.ylabel('channel %d'%i)
    plt.plot([0, len(out_np[i])], thrs[i]*np.ones(2), 'r')
    plt.plot(out_np[i])

out_np_bool = out_np > thrs[:,None]

led_on = []
for i in range(out_np_bool.shape[0]):
    ttl_start, ttl_dur = detectTTL(out_np_bool[i])
    ind_valid = ttl_dur> 1*25
    led_on.append([ttl_start[ind_valid], ttl_dur[ind_valid]])
led_on = np.array(led_on)

led_on_start = led_on[:,0,:]
jit = (led_on_start - led_on_start.min(axis=0, keepdims=True)).mean(axis=1)
jit -= jit.min()
jit_int = np.round(jit-0.1).astype(int) #需要裁剪的帧数，滞后的帧数

plt.subplot(npannel,1,1)
plt.title('jit_int:'+','.join(str(i) for i in jit_int))
plt.savefig(vfile.replace('.mp4', '_lagAmongCams.jpg'))
