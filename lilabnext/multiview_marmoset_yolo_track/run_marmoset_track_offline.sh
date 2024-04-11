conda activate mmdet
project_ball_calib=/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-1-31_sync/marmoset
vfile=2024-01-31_16-38-19
cd $project_ball_calib

setupname=frank
checkpoint=/home/liying_lab/chenxinfeng/DATA/ultralytics/work_dirs/yolov8_det_640x640_marmoset/weights/last.singleton.engine
python -m lilab.yolo_det.s1_video2matpkl --setupname $setupname --checkpoint $checkpoint $vfile.mp4 
