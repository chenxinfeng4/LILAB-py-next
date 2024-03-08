#%% 在linux
YUN_DIR=`w2l "\\liying.cibr.ac.cn\Data_Temp\Chenxinfeng\marmoset_camera3_cxf\realtime_model"`
model_onnx=/home/liying_lab/chenxinfeng/DATA/mmpose/work_dirs/res50_coco_toy_640x480/latest.full.onnx
calibpkl=//mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2023-11-22-calib/*.calibpkl
model_name='toy'

YUN_model_onnx=$YUN_DIR/${model_name}latest.full.onnx
YUN_calibpkl=$YUN_DIR/ball.calibpkl
cp $model_onnx $YUN_model_onnx
cp $calibpkl $YUN_calibpkl

#%% 在windows
set model_name=toy

conda activate open-mmlab
set W_YUN_DIR=\\liying.cibr.ac.cn\Data_Temp\Chenxinfeng\marmoset_camera3_cxf\realtime_model
copy /y %W_YUN_DIR%\%model_name%latest.full.onnx D:\
copy /y %W_YUN_DIR%\ball.calibpkl D:\

trtexec --onnx=D:/%model_name%latest.full.onnx ^
    --saveEngine=D:/%model_name%latest.full.engine ^
    --timingCacheFile=D:/%model_name%.cache.txt ^
    --fp16 --workspace=3072 ^
    --shapes=input_1:3x3x480x640


python -m lilabnext.multview_marmoset_track.t1_realtime_position ^
    --checkpoint D:/%model_name%latest.full.engine --calibpkl D:/ball.calibpkl

python -m lilabnext.multview_marmoset_track.t1_realtime_view --checkpoint D:/toylatest.full.engine --calibpkl D:/ball.calibpkl
python -m lilabnext.multview_marmoset_track.t1_realtime_position --checkpoint D:/toylatest.full.engine --calibpkl D:/ball.calibpkl
