#%%
import numpy as np
import torch
from lilabnext.camera_sync.mkv_videos_reader import get_mkv_reader

from lilab.yolo_det.s1_video2matpkl import (
    DataSet, post_cpu, create_trtmodule, box2cs, mid_gpu, checkpoint
)
import argparse
import warnings
import pickle
import os
import os.path as osp
import tqdm


def main(video_file, checkpoint):
    feature_in_wh = [640, 480]
    vid = get_mkv_reader(video_file, pix_fmt='rgb24',
                        resize = feature_in_wh, resize_keepratio=False)
    view_w, view_h = vid.vid_list[0].origin_width, vid.vid_list[0].origin_height
    print('view_w, h', view_w, view_h)
    dataset = DataSet(vid)
    center, scale = box2cs(np.array([0,0,view_w,view_h]), feature_in_wh, keep_ratio=False)
    dataset_iter = iter(dataset)
    input_shape = dataset.coord_NCHW_idx_ravel.shape
    trt_model, img_NCHW, outputs = create_trtmodule(checkpoint, input_shape)
    nview = img_NCHW.shape[0]

    keypoints_xyp = []
    for idx in tqdm.trange(-1, len(dataset)-1):
        outputs_wait = mid_gpu(trt_model, img_NCHW)              # t
        img_NCHW_next, img_preview_next = next(dataset_iter)     # t+1
        img_NCHW, img_preview = img_NCHW_next, img_preview_next  # t+1
        torch.cuda.current_stream().synchronize()                # t
        outputs = outputs_wait                                   # t
        if idx<=-1: continue
        kpt2d = post_cpu(outputs, center, scale, feature_in_wh)  # t
        keypoints_xyp.append(kpt2d)

    outputs = mid_gpu(trt_model, img_NCHW)
    kpt2d = post_cpu(outputs, center, scale, feature_in_wh)
    keypoints_xyp.append(kpt2d)

    keypoints_xyp = np.array(keypoints_xyp).transpose(1,0,2,3)#(nview, T, K, 3)
    # assert np.mean(keypoints_xyp[...,2].ravel()<0.4) < 0.1, 'Too many nan in keypoints_xyp !'
    if np.median(keypoints_xyp[...,2])<0.4:
        warnings.warn('Too many nan in keypoints_xyp !')
        # assert np.median(keypoints_xyp[...,2])>0.4, 'Too many nan in keypoints_xyp !'

    info = {'vfile': video_file, 'nview': nview, 'fps':  dataset.vid.fps}
    outpkl = os.path.splitext(video_file)[0] + '.mkv.matpkl'
    outdict = dict(
        keypoints = keypoints_xyp,
        views_xywh = [[0,0,view_w,view_h]]*nview,
        info = info
    )
    pickle.dump(outdict, open(outpkl, 'wb'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('video_path', type=str, help='path to video or folder')
    parser.add_argument('--checkpoint', type=str, default=checkpoint)
    arg = parser.parse_args()

    video_path, checkpoint = arg.video_path, arg.checkpoint
    print("checkpoint:", checkpoint)
    assert osp.isfile(video_path), 'video_path not exists'
    main(video_path, checkpoint)
