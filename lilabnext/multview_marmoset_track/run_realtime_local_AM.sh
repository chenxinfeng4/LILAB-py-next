# 实时小球
checkpoint=/home/liying_lab/chenxinfeng/DATA/mmpose/work_dirs/res50_coco_ball_640x480/latest.full.engine
calibpkl=`w2l "\\liying.cibr.ac.cn\Data_Temp\Chenxinfeng\marmoset_camera3_cxf\2023-11-22-calib\ball_move_cam1.calibpkl"`

python -m lilabnext.multview_marmoset_track.t1_realtime_position \
    --checkpoint $checkpoint \
    --calibpkl $calibpkl


# 实时猴子
checkpoint=/home/liying_lab/chenxinfeng/DATA/mmpose/work_dirs/res50_coco_toy_640x480/latest.full.engine
calibpkl=`w2l "\\liying.cibr.ac.cn\Data_Temp\Chenxinfeng\marmoset_camera3_cxf\2023-11-22-calib\ball_move_cam1.calibpkl"`

python -m lilabnext.multview_marmoset_track.t1_realtime_position \
    --checkpoint $checkpoint \
    --calibpkl $calibpkl
