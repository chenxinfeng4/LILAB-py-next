# python -m lilab.multiview_scripts_dev.s1_ballvideo2matpkl_full_faster  /mnt/liying.cibr.ac.cn_Data_Temp/multiview_9/VPAxWT/DAY75/SOLO/
# %%
import argparse
import os
import numpy as np
import tqdm
import torch
import pickle
import mmcv
from torch2trt import TRTModule
import itertools
from lilab.mmpose_dev.a2_convert_mmpose2engine import findcheckpoint_trt
from torch2trt.torch2trt import torch_dtype_from_trt
from lilab.multiview_scripts_dev.s1_ballvideo2matpkl_full_realtimecam import (
    get_max_preds_gpu, transform_preds, pre_cpu, mid_gpu, box2cs, 
    preview_resize
)
import os.path as osp
import glob
import warnings
from lilabnext.multiview_zyy.video_set_reader import VideoSetReader


#%%
class DataSet: 
    def __init__(self, vid:VideoSetReader):
        self.coord_NCHW_idx_ravel = np.zeros(vid.out_numpy_shape, dtype=np.uint8).transpose(0,3,1,2)
        self.vid = vid
        self.input_trt_shape = self.coord_NCHW_idx_ravel.shape
    
    def __len__(self):
        return len(self.vid)
        
    def __iter__(self):
        while True:
            ret, img_NHWC = self.vid.read()
            if not ret:
                print('End of video')
                raise StopIteration
            img_preview = np.zeros((preview_resize[1],preview_resize[0],3), dtype=np.uint8)
            img_NCHW = img_NHWC.transpose(0,3,1,2)
            yield img_NCHW, img_preview


class MyWorker():
    def __init__(self):
        super().__init__()
        self.id = getattr(self, 'id', 0)
        self.cuda = getattr(self, 'cuda', 0)

    def compute(self, args):
        config, video_file, checkpoint, nview = args
        cfg = mmcv.Config.fromfile(config)
        feature_in_wh = np.array(cfg.data_cfg['image_size'])
        vid = VideoSetReader(video_file, nvideo=nview, pix_fmt='rgb24',
                             resize = feature_in_wh, resize_keepratio=False)
        view_w, view_h = vid.vid_list[0].origin_width, vid.vid_list[0].origin_height
        print('view_w, h', view_w, view_h)
        dataset = DataSet(vid)
        center, scale = box2cs(np.array([0,0,view_w,view_h]), feature_in_wh, keep_ratio=False)
        dataset_iter = iter(dataset)

        count_range = range(dataset.__len__()) if hasattr(dataset, '__len__') else itertools.count()

        with torch.cuda.device(self.cuda):
            trt_model = TRTModule()
            trt_model.load_from_engine(checkpoint)
            idx = trt_model.engine.get_binding_index(trt_model.input_names[0])
            input_dtype = torch_dtype_from_trt(trt_model.engine.get_binding_dtype(idx))
            input_shape = tuple(trt_model.context.get_binding_shape(idx))
            if input_shape[0]==-1:
                assert input_shape[1:]==dataset.coord_NCHW_idx_ravel.shape[1:]
                input_shape = dataset.coord_NCHW_idx_ravel.shape
            else:
                assert input_shape==dataset.coord_NCHW_idx_ravel.shape
            img_NCHW = np.ones(input_shape)
            img_preview = np.zeros((*preview_resize,3))
            heatmap = mid_gpu(trt_model, img_NCHW, input_dtype)
            # img_NCHW, img_preview = pre_cpu(dataset_iter)
            keypoints_xyp = []
            for idx, _ in enumerate(tqdm.tqdm(count_range, 
                                              desc='worker[{}]'.format(self.id),
                                              position=int(self.id)), 
                                    start=-1):
                heatmap_wait = mid_gpu(trt_model, img_NCHW, input_dtype) # t
                img_NCHW_next, img_preview_next = pre_cpu(dataset_iter)  # t+1
                img_NCHW, img_preview = img_NCHW_next, img_preview_next  # t+1
                torch.cuda.current_stream().synchronize()                # t
                heatmap = heatmap_wait                                   # t
                if idx<=-1: continue
                kpt2d = post_cpu(None, heatmap, center, scale, None, img_preview, None) # t
                keypoints_xyp.append(kpt2d)

            heatmap = mid_gpu(trt_model, img_NCHW, input_dtype)
            kpt2d = post_cpu(None, heatmap, center, scale, None, img_preview, None)
            keypoints_xyp.append(kpt2d)
        
        # save data to pickle file
        keypoints_xyp = np.array(keypoints_xyp).transpose(1,0,2,3)#(nview, T, K, 3)
        # assert np.mean(keypoints_xyp[...,2].ravel()<0.4) < 0.1, 'Too many nan in keypoints_xyp !'
        if np.median(keypoints_xyp[...,2])>0.4:
            warnings.warn('Too many nan in keypoints_xyp !')
            # assert np.median(keypoints_xyp[...,2])>0.4, 'Too many nan in keypoints_xyp !'

        info = {'vfile': video_file, 'nview': nview, 'fps':  dataset.vid.fps}
        outpkl = os.path.splitext(video_file)[0] + '.matpkl'
        outdict = dict(
            keypoints = keypoints_xyp,
            views_xywh = [None]*nview,
            info = info
        )
        pickle.dump(outdict, open(outpkl, 'wb'))
        print('python -m lilab.multiview_scripts_dev.s2_matpkl2ballpkl',
            outpkl, '--time 1 2 3 4 5')
        print('python -m lilab.multiview_scripts_dev.s5_show_calibpkl2video', outpkl)


def post_cpu(camsize, heatmap, center, scale, views_xywh, img_preview, calibobj):
    N, K, H, W = heatmap.shape
    preds, maxvals = get_max_preds_gpu(heatmap)
    preds = transform_preds(
                preds, center, scale, [W, H], use_udp=False)
    keypoints_xyp = np.concatenate((preds, maxvals), axis=-1) #(N, K, xyp)
    return keypoints_xyp


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('video_path', type=str, help='path to video or folder')
    parser.add_argument('--pannels', default=4, type=int, help='crop views')
    parser.add_argument('--config', type=str, default=None)
    parser.add_argument('--checkpoint', type=str, default=None)
    arg = parser.parse_args()

    nviews = arg.pannels
    video_path, config, checkpoint = arg.video_path, arg.config, arg.checkpoint
    assert config is not None
    if checkpoint is None:
        checkpoint = findcheckpoint_trt(config, 'latest.full.engine')
    print("config:", config)
    print("checkpoint:", checkpoint)

    assert osp.exists(video_path), 'video_path not exists'
    if osp.isfile(video_path):
        video_path = [video_path]
    elif osp.isdir(video_path):
        video_path = glob.glob(osp.join(video_path, '*.mp4'))
        video_path = [v for v in video_path
                      if 'sktdraw' not in v and
                         'com3d' not in v and
                         'mask' not in v]
        assert len(video_path) > 0, 'no video found'
    else:
        raise ValueError('video_path is not a file or folder')
    
    args_iterable = itertools.product([config], video_path, [checkpoint], [nviews])
    worker = MyWorker()
    for args in args_iterable:
        worker.compute(args)
