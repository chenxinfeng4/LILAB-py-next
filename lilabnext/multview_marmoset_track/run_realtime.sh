#!/bin/bash
config=~/DATA/mmpose/res50_coco_ball_640x480.py
calibpkl=/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/f1.recalibpkl
python -m lilabnext.multview_marmoset_track.t1_realtime_position \
    --config $config --calibpkl $calibpkl
