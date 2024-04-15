# python -m lilab.next.multiview_marmoset_yolo_track.t1_realtime_position --checkpoint ENGINE --calibpkl aligncalibpkl
import argparse
import numpy as np
import tqdm
import time
import ffmpegcv
import threading
import itertools
from torch2trt.pycuda2trt import TRTModule
from lilab.multiview_scripts_dev.s1_ballvideo2matpkl_full_realtimecam import pre_cpu
import lilabnext.multiview_marmoset_yolo_track.t1a_realtime_position_daemon_rpc as sockserver
from ffmpegcv import ReadLiveLast
import pickle

from lilab.yolo_det.convert_pt2onnx import singleton

camsize = (640,480)
yolo_pthr = 0.4
rtsp_streams = ['rtsp://admin:2019Cibr@192.168.1.142:554/Streaming/Channels/102',
                'rtsp://admin:2019Cibr@192.168.1.137:554/Streaming/Channels/102',
                'rtsp://admin:2019Cibr@192.168.1.141:554/Streaming/Channels/102',
                'rtsp://admin:2019Cibr@192.168.1.103:554/Streaming/Channels/102',
                'rtsp://admin:2019Cibr@192.168.1.143:554/Streaming/Channels/102']


def post_cpu(outputs, reverse_to_src_index):
    boxes, scores = singleton(outputs)
    boxes_center = (boxes[...,[0,1]] + boxes[...,[2,3]])/2
    keypoints_xy = reverse_to_src_index(boxes_center) #nview,nanimal,2
    keypoints_p = np.squeeze(scores) #nview,nanimal
    keypoints_xy[keypoints_p < yolo_pthr] = np.nan
    return keypoints_xy


def mid_gpu(trt_model, img_NCHW):
    batch_img = img_NCHW.astype(np.float32)
    outputs = trt_model(batch_img)
    return outputs


class DataSet: 
    def __init__(self, rtsp_streams, camsize_wh, pix_fmt):
        out_numpy_shape = (len(rtsp_streams), camsize_wh[1], camsize_wh[0], 3)
        coord_NCHW_idx_ravel = np.zeros(out_numpy_shape, dtype=np.uint8).transpose(0,3,1,2)
        self.vid = ([ReadLiveLast(ffmpegcv.VideoCaptureStreamRT, r, pix_fmt=pix_fmt)
                        for r in rtsp_streams])
        self.input_trt_shape = coord_NCHW_idx_ravel.shape
    
    def __iter__(self):
        while True:
            rets, imgs = [], []
            for v in self.vid:
                ret, img = v.read()
                rets.append(ret); imgs.append(img)
            assert all(rets)
            img_NHWC = np.array(imgs)
            img_preview = ModuleNotFoundError
            img_NCHW = img_NHWC.transpose(0,3,1,2)
            yield img_NCHW, img_preview


def main(rtsp_streams:str, checkpoint:str, ballcalib:str, iclass:int):
    rpc_client = sockserver.create_client()

    ba_poses = pickle.load(open(ballcalib, 'rb'))['ba_poses']
    rpc_client.ba_poses({i: ba_poses[i] for i in range(len(rtsp_streams))})
    rpc_client.ba_poses_full(ba_poses)

    dataset = DataSet(rtsp_streams, camsize_wh=camsize, pix_fmt='rgb24')
    dataset.reverse_to_src_index = lambda x: x
    dataset_iter = iter(dataset)
    print("Well setup VideoCapture")

    count_range = itertools.count()

    trt_model = TRTModule()
    trt_model.load_from_engine(checkpoint)
    idx = trt_model.engine.get_binding_index(trt_model.input_names[0])
    input_shape = tuple(trt_model.context.get_binding_shape(idx))
    if input_shape[0]==-1:
        assert input_shape[1:]==dataset.input_trt_shape[1:]
        input_shape = dataset.input_trt_shape
    else:
        assert input_shape==dataset.input_trt_shape
    img_NCHW = np.zeros(input_shape)
    outputs = mid_gpu(trt_model, img_NCHW)
    num_joints = outputs[1].shape[-1]

    for iframe, _ in enumerate(tqdm.tqdm(count_range, desc='RT')):
        if sockserver.get_number_of_connections()<=1 and iframe % 100 != 0:
            time.sleep(0.1)
            continue
        img_NCHW, img_preview = pre_cpu(dataset_iter)
        outputs = mid_gpu(trt_model, img_NCHW)
        keypoints_xy = post_cpu(outputs, dataset.reverse_to_src_index)
        rpc_client.process_p2d(keypoints_xy, iclass, iframe)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', type=str, default=None)
    parser.add_argument('--calibpkl', type=str, default=None)
    parser.add_argument('--createport', type=int, default=8090)
    parser.add_argument('--iclass', type=int, default=None)
    args = parser.parse_args()

    checkpoint, calibpkl = args.checkpoint, args.calibpkl
    print("checkpoint:", checkpoint)

    sockserver.PORT = args.createport
    threading.Thread(target=sockserver.serve_forever).start()
    main(rtsp_streams, checkpoint, calibpkl, args.iclass)
