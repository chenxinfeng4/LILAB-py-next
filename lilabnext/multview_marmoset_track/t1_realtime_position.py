
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
    mid_gpu, pre_cpu, findcheckpoint_trt
)
from lilab.dannce_realtime.com3d_realtime import post_cpu
import ffmpegcv
import multiprocessing
from multiprocessing import Array, Queue, Lock
import time
from .s1_ballvideo2matpkl_full_faster import DataSet
from .video_set_reader import StreamRTSetReader
from .msg_file_io import write_msg, write_calibpkl_msg

gpu_id = 2


def show_com3d(*args):
    pass

rtsp_streams = ['rtsp://admin:2019Cibr@10.50.5.252:8091/Streaming/Channels/102',
                'rtsp://admin:2019Cibr@10.50.5.252:8092/Streaming/Channels/102',
                'rtsp://admin:2019Cibr@10.50.5.252:8093/Streaming/Channels/102']

class MyWorker:
    def __init__(self, config:str, rtsp_streams:str, checkpoint:str, ballcalib:str):
        super().__init__()
        self.cuda = getattr(self, 'cuda', gpu_id)
        self.checkpoint = checkpoint
        self.calibobj = CalibPredict(ballcalib) if ballcalib else None
        write_calibpkl_msg(self.calibobj.poses)
        camsize = (640,480)
        
        preview_ipannel = 0
        self.preview_ipannel = preview_ipannel
        self.vidout = ffmpegcv.VideoWriterNV('/mnt/liying.cibr.ac.cn_Data_Temp/multiview_9/chenxf/out_com3d.mp4',
                                             codec = 'h264', fps=30)
        vid = StreamRTSetReader(rtsp_streams, camsize_wh=camsize, pix_fmt='rgb24')

        self.video_file = rtsp_streams
        self.vid = vid
        self.camsize = camsize
        self.canvas_hw = (camsize[1], camsize[0])
        cfg = mmcv.Config.fromfile(config)
        self.num_joints = cfg.data_cfg['num_joints']
        self.dataset = DataSet(self.vid)
        self.dataset.reverse_to_src_index = lambda x: x

        self.calibobj.last_keypoints_xyz_ba = np.zeros((self.num_joints, 3))
        self.dataset_iter = iter(self.dataset)
        self.NFRAME = 10
        self.mem_canvas_img = camsize[0] * camsize[1]
        self.mem_joints_3d = self.num_joints * 3 * 4 #3D, np.float32
        self.mem_iframe = 4 #np.int32
        # self.np_array = np.frombuffer(self.shared_array.get_obj(), dtype=np.uint8).reshape((self.NFRAME, -1))
        # self.np_array_canvas_img = self.np_array[:, :self.mem_canvas_img]
        # self.np_array_joints_3d = self.np_array[:, self.mem_canvas_img: self.mem_canvas_img + self.mem_joints_3d]
        # self.np_array_iframe = self.np_array[:, self.mem_canvas_img + self.mem_joints_3d: self.mem_canvas_img + self.mem_joints_3d + self.mem_iframe]
        print("Well setup VideoCapture")
    
    def encode_array(self, iframe:int, canvas:np.array, kpt_xyz:np.array):
        iframe += self.NFRAME
        data_id = (iframe+self.NFRAME) % self.NFRAME
        with self.lock:
            self.np_array_canvas_img[data_id][:] = canvas.ravel().view(np.uint8)
            self.np_array_joints_3d[data_id][:] = kpt_xyz.ravel().view(np.uint8)
            self.np_array_iframe[data_id][:] = np.int32([iframe]).view(np.uint8)

        if self.q.full():
            self.q.get()
            # print('Droping')
        self.q.put(data_id)

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
                pbar.update(1)
                heatmap_wait = mid_gpu(trt_model, img_NCHW, input_dtype)
                img_NCHW_next, img_preview_next = pre_cpu(dataset_iter)
                torch.cuda.current_stream().synchronize()
                heatmap = heatmap_wait
                if iframe>-1: 
                    keypoints_xyz_ba, keypoints_xy_ba, keypoints_xy, keypoints_xyp = post_cpu(heatmap, self.dataset.reverse_to_src_index, self.calibobj)
                    show_com3d(img_preview, self.preview_ipannel, keypoints_xy_ba, keypoints_xy, self.vidout)
                    write_msg((iframe, 123, 456, 789))
                    write_msg(','.join([str(s) for s in [iframe, *keypoints_xyp.ravel()]]), 'com2d', with_date=False)
                    write_msg(','.join([str(s) for s in [iframe, *keypoints_xy_ba.ravel()]]), 'com2d_ba', with_date=False)
                    # self.encode_array(iframe, img_next, keypoints_xyz_ba)
                img_NCHW, img_preview = img_NCHW_next, img_preview_next

        self.vidout.release()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default=None)
    parser.add_argument('--checkpoint', type=str, default=None)
    parser.add_argument('--calibpkl', type=str, default=None)
    arg = parser.parse_args()

    config, checkpoint, calibpkl = arg.config, arg.checkpoint, arg.calibpkl
    assert config is not None
    if checkpoint is None:
        checkpoint = findcheckpoint_trt(config, trtnake='latest.full.engine')
    print("config:", config)
    print("checkpoint:", checkpoint)

    worker = MyWorker(config, rtsp_streams, checkpoint, calibpkl)
    worker.compute()
