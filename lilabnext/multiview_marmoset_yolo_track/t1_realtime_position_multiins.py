import argparse
import numpy as np
import tqdm
import time
import threading
import itertools
from torch2trt.pycuda2trt import TRTModule
from lilab.multiview_scripts_dev.s1_ballvideo2matpkl_full_realtimecam import pre_cpu
import lilabnext.multiview_marmoset_yolo_track.t1a_realtime_position_daemon_rpc as sockserver
import pickle
from lilabnext.multiview_marmoset_yolo_track.t1_realtime_position import (
    mid_gpu, DataSet, rtsp_streams, camsize, yolo_pthr)

from lilab.yolo_det.s1_video2matpkl_multianimal import (post_cpu, box2cs)


def main(rtsp_streams:str, checkpoint:str, ballcalib:str, iclass:int, nins:int):
    rpc_client = sockserver.create_client()

    ba_poses = pickle.load(open(ballcalib, 'rb'))['ba_poses']
    rpc_client.ba_poses({i: ba_poses[i] for i in range(len(rtsp_streams))})
    rpc_client.ba_poses_full(ba_poses)
    rpc_client.nins(nins)

    dataset = DataSet(rtsp_streams, camsize_wh=camsize, pix_fmt='rgb24')
    dataset.reverse_to_src_index = lambda x: x
    feature_in_wh = camsize
    center, scale = box2cs(np.array([0,0,*camsize]), feature_in_wh, keep_ratio=False)
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

    for iframe, _ in enumerate(tqdm.tqdm(count_range, desc='RT')):
        if sockserver.get_number_of_connections()<=1 and iframe % 100 != 0:
            time.sleep(0.1)
            continue
        img_NCHW, img_preview = pre_cpu(dataset_iter)
        outputs = mid_gpu(trt_model, img_NCHW)
        keypoints_xyp = post_cpu(outputs, center, scale, feature_in_wh, iclass, nins)
        p2d_shuffle = keypoints_xyp[:,:,:2]
        p2d_shuffle[keypoints_xyp[:,:,2] < yolo_pthr] = np.nan
        rpc_client.p2d(iframe, p2d_shuffle)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', type=str, default=None)
    parser.add_argument('--calibpkl', type=str, default=None)
    parser.add_argument('--createport', type=int, default=8090)
    parser.add_argument('--iclass', type=int, default=0)
    parser.add_argument('--ninstance', type=int, default=2)
    args = parser.parse_args()

    checkpoint, calibpkl = args.checkpoint, args.calibpkl
    print("checkpoint:", checkpoint)

    sockserver.PORT = args.createport
    threading.Thread(target=sockserver.serve_forever).start()
    main(rtsp_streams, checkpoint, calibpkl, args.iclass, args.ninstance)
