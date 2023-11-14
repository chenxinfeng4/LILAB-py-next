
import argparse
import numpy as np
import tqdm
import torch
import mmcv
import ffmpegcv
from torch2trt import TRTModule
import itertools
from multiview_calib.calibpkl_predict import CalibPredict
from torch2trt.torch2trt import torch_dtype_from_trt
from lilab.multiview_scripts_dev.comm_functions import get_max_preds_gpu
from lilab.multiview_scripts_dev.s1_ballvideo2matpkl_full_realtimecam import (
    mid_gpu, pre_cpu
)
import ffmpegcv
import threading
from .s1_ballvideo2matpkl_full_faster import DataSet
from .video_set_reader import StreamRTSetReader
from .msg_file_io import write_msg, write_calibpkl_msg
from lilabnext.multview_marmoset_track.t1c_realtime_position_daemon_socket import serve_forever
from ffmpegcv.ffmpeg_noblock import ReadLiveLast

gpu_id = 0


def show_com3d(*args):
    pass

rtsp_streams = ['rtsp://admin:2019Cibr@10.50.5.252:8091/Streaming/Channels/102',
                'rtsp://admin:2019Cibr@10.50.5.252:8092/Streaming/Channels/102',
                'rtsp://admin:2019Cibr@10.50.5.252:8093/Streaming/Channels/102']


def post_cpu(heatmap, reverse_to_src_index, calibobj:CalibPredict):
    assert calibobj is not None
    keypoints_xy_origin, keypoints_p = get_max_preds_gpu(heatmap)
    keypoints_xy = reverse_to_src_index(keypoints_xy_origin) #nview,nanimal,2
    keypoints_p = np.squeeze(keypoints_p) #nview,nanimal
    # thr
    thr = 0.4
    indmiss = keypoints_p < thr
    keypoints_xyp = np.concatenate([keypoints_xy, keypoints_p[:,None,None]], axis=-1)
    keypoints_xy[indmiss] = np.nan

    # ba
    keypoints_xyz_ba = calibobj.p2d_to_p3d(keypoints_xy)  #nanimal, 3
    isnan = np.isnan(keypoints_xyz_ba)
    if np.any(isnan):
        keypoints_xyz_ba[isnan] = calibobj.last_keypoints_xyz_ba[isnan]
    calibobj.last_keypoints_xyz_ba = keypoints_xyz_ba
    keypoints_xy_ba = calibobj.p3d_to_p2d(keypoints_xyz_ba) #nview, nanimal, 2
    return keypoints_xyz_ba, keypoints_xy_ba, keypoints_xy, keypoints_xyp


class DataSet: 
    def __init__(self, rtsp_streams, camsize_wh, pix_fmt):
        out_numpy_shape = (len(rtsp_streams), camsize_wh[1], camsize_wh[0], 3)
        self.coord_NCHW_idx_ravel = np.zeros(out_numpy_shape, dtype=np.uint8).transpose(0,3,1,2)
        self.vid = [ffmpegcv.VideoCaptureStreamRT(rtsp_streams[0], camsize_wh=camsize_wh, pix_fmt=pix_fmt)]
        self.vid.extend([ReadLiveLast(ffmpegcv.VideoCaptureStreamRT, r, camsize_wh=camsize_wh, pix_fmt=pix_fmt)
                        for r in rtsp_streams[1:]])
        self.input_trt_shape = self.coord_NCHW_idx_ravel.shape
    
    def __iter__(self):
        while True:
            rets, imgs = [], []
            for v in self.vid:
                ret, img = v.read()
                rets.append(ret); imgs.append(img)
            assert all(rets)
            img_NHWC = np.array(imgs)
            img_preview = np.zeros((800,1280,3), dtype=np.uint8)
            img_NCHW = img_NHWC.transpose(0,3,1,2)
            yield img_NCHW, img_preview


class MyWorker:
    def __init__(self, rtsp_streams:str, checkpoint:str, ballcalib:str):
        super().__init__()
        self.cuda = getattr(self, 'cuda', gpu_id)
        self.checkpoint = checkpoint
        self.calibobj = CalibPredict(ballcalib) if ballcalib else None
        write_calibpkl_msg(self.calibobj.poses)
        camsize = (640,480)
        
        preview_ipannel = 0
        self.preview_ipannel = preview_ipannel
        vid = StreamRTSetReader(rtsp_streams, camsize_wh=camsize, pix_fmt='rgb24')

        self.video_file = rtsp_streams
        self.vid = vid
        self.camsize = camsize
        self.canvas_hw = (camsize[1], camsize[0])
        self.num_joints = 1
        self.dataset = DataSet(rtsp_streams, camsize_wh=camsize, pix_fmt='rgb24')
        self.dataset.reverse_to_src_index = lambda x: x

        self.calibobj.last_keypoints_xyz_ba = np.zeros((self.num_joints, 3))
        self.dataset_iter = iter(self.dataset)
        print("Well setup VideoCapture")
    
    def compute(self):
        dataset, dataset_iter = self.dataset, self.dataset_iter
        count_range = itertools.count()
        with torch.cuda.device(self.cuda):
            trt_model = TRTModule()
            trt_model.load_from_engine(self.checkpoint)
            idx = trt_model.engine.get_binding_index(trt_model.input_names[0])
            input_dtype = torch_dtype_from_trt(trt_model.engine.get_binding_dtype(idx))
            input_shape = tuple(trt_model.context.get_binding_shape(idx))
            if input_shape[0]==-1:
                assert input_shape[1:]==self.dataset.input_trt_shape[1:]
                input_shape = self.dataset.input_trt_shape
            else:
                assert input_shape==self.dataset.input_trt_shape
            img_NCHW = np.zeros(input_shape)
            heatmap = mid_gpu(trt_model, img_NCHW, input_dtype)

            pbar = tqdm.tqdm(count_range, desc='loading')
            for iframe, _ in enumerate(count_range, start=-1):
                img_NCHW, img_preview = pre_cpu(dataset_iter)
                pbar.update(1)
                heatmap_wait = mid_gpu(trt_model, img_NCHW, input_dtype)
                torch.cuda.current_stream().synchronize()
                heatmap = heatmap_wait
                if iframe>-1: 
                    keypoints_xyz_ba, keypoints_xy_ba, keypoints_xy, keypoints_xyp = post_cpu(heatmap, self.dataset.reverse_to_src_index, self.calibobj)
                    write_msg((iframe, 123, 456, 789))
                    write_msg(','.join([str(s) for s in [iframe, *keypoints_xyp.ravel()]]), 'com2d', with_date=False)
                    write_msg(','.join([str(s) for s in [iframe, *keypoints_xy_ba.ravel()]]), 'com2d_ba', with_date=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', type=str, default=None)
    parser.add_argument('--calibpkl', type=str, default=None)
    arg = parser.parse_args()

    checkpoint, calibpkl = arg.checkpoint, arg.calibpkl
    print("checkpoint:", checkpoint)

    threading.Thread(target=serve_forever).start()
    worker = MyWorker(rtsp_streams, checkpoint, calibpkl)
    worker.compute()
