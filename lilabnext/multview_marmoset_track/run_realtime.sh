#!/bin/bash
checkpoint=/home/liying_lab/chenxinfeng/DATA/mmpose/work_dirs/res50_coco_ball_640x480/latest.full.engine
calibpkl=/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/f1.recalibpkl

python -m lilabnext.multview_marmoset_track.t1_realtime_position \
    --checkpoint $checkpoint \
    --calibpkl $calibpkl
