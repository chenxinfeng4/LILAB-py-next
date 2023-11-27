#%% 在linux
YUN_DIR=`w2l "\\liying.cibr.ac.cn\Data_Temp\Chenxinfeng\marmoset_camera3_cxf\realtime_model"`
model_onnx=/home/liying_lab/chenxinfeng/DATA/mmpose/work_dirs/res50_coco_ball_640x480/latest.full.onnx
calibpkl=/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2023-11-22-calib/*.calibpkl

model_trt=/home/liying_lab/chenxinfeng/DATA/mmpose/work_dirs/res50_coco_ball_640x480/latest.full.engine

python -m lilabnext.multview_marmoset_track.t1_realtime_position \
    --checkpoint $model_trt --calibpkl $calibpkl