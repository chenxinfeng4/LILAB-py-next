#%% 0. 【必须】 初始化
# intrin1.mp4 2.mp4 3.mp4
conda activate mmdet
project_ball_calib=/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-1-31_sync/ballmove/temp
cd $project_ball_calib

#%% 1. 【可选】从头开始，矫正内参
checkboard_move_mp4=`ls checkboard_move_cam*.mp4`
echo "$checkboard_move_mp4" | xargs -n 1 -P 0 python -m lilab.cvutils_new.extract_frames --npick 100
ncam=`echo "$checkboard_move_mp4" | sort -r | sed -n '1 s/.*cam\([1-9]\).mp4/\1/p'`

for ((i=0; i<=$ncam-1; i++)); do
    mkdir -p intrinsic_calib_frames/$i 
    mv outframes/checkboard_move_cam$((i+1))*.jpg intrinsic_calib_frames/$i
done
rm -r outframes

python -m lilabnext.multview_marmoset_track.intrinsic_utils intrinsic_calib_frames/ --board_size 11 8
#'将内参的 intrinsic_calib_frames/intrinsics_calib.json 拷贝到 lilab/cameras_setup/_get_calibinfo.py'

#%% 2. 【可选】 从头开始，视频抽帧，打标
# f1.mp4 2.mp4 3.mp4
setupname=frank2
ls ballmove.mp4 | xargs -n 1 python -m lilab.cvutils_new.extract_frames_pannel_crop_random --npick 100 --setupname $setupname
mv outframes/ ball_frames/

#打开LABELME 打标小球，Open Dir，选择ball_640x480_20231124_marmosetcam文件夹，右键create point...全部结束后直接关闭，改下面ball_640x480_20231124日期， 执行
rm `comm -3 <(ls -1 ball_frames/*.jpg | sort) <(ls -1 ball_frames/*.json | sed s/json/jpg/ | sort)`
project_nake_name=ball_20240329
mv ball_frames $project_nake_name
target_dataset=/home/liying_lab/chenxinfeng/DATA/ultralytics/data/ball_rg/$project_nake_name
python -m lilab.yolo_det.convert_labelme2yoloDet --json_dir $project_nake_name --val_size 0.2 --target_dir $target_dataset


# 添加新的数据到里面
mfile='yolov8n_det_640_ballrg.py'
mfile_nake=${mfile%.*}

cd /home/liying_lab/chenxinfeng/DATA/ultralytics/
echo $target_dataset/dataset.yaml
echo $mfile   #然后 ctrl + 鼠标左键，进入yolov8l_det_640_ballrg.py， 在13行的 data="data/ball_rg/dataset.yaml" 为最新的路径. 修改epoch
# vim $mfile

# 开始训练
source activate open-mmlab
python $mfile

# 模型文件转化为 onnx， tensorrt。提升推断速度
python -m lilab.yolo_det.convert_pt2onnx work_dirs/${mfile_nake}/weights/last.pt --dynamic
source activate mmdet
trtexec --onnx=work_dirs/${mfile_nake}/weights/last.singleton.onnx \
    --fp16 --saveEngine=work_dirs/${mfile_nake}/last.singleton.engine \
    --timingCacheFile=work_dirs/${mfile_nake}/.cache.txt \
    --workspace=3072 --optShapes=input_1:4x3x480x640 \
    --minShapes=input_1:1x3x480x640 --maxShapes=input_1:9x3x480x640


#%% 3. 【必须】 外参矫正 确认文件名
cd $project_ball_calib
# vfile=ball_move_cam1
vfile=ball_move
setupname=frank2
checkpoint=/home/liying_lab/chenxinfeng/DATA/ultralytics/work_dirs/yolov8n_det_640_ballrg/last.singleton.engine

python -m lilab.yolo_det.s1_video2matpkl --setupname $setupname --checkpoint $checkpoint $vfile.mp4 

# python -m lilabnext.multview_marmoset_track.s5_show_calibpkl2video $vfile.matpkl
python -m lilab.multiview_scripts_dev.s5_show_calibpkl2video $vfile.matpkl


tball=" 0 0 0 0 10 " # 没有用，只是占位
# python -m lilabnext.multiview_zyy.s2_matpkl2ballpkl $vfile.matpkl  --time  $tball --force-setupname  $setupname
python -m lilab.multiview_scripts_dev.s2_matpkl2ballpkl $vfile.matpkl  --time  $tball --force-setupname  $setupname --nchoose 2000
python -m lilab.multiview_scripts_dev.s3_ballpkl2calibpkl $vfile.ballpkl --skip-camera-intrinsic --skip-global 
python -m lilabnext.multiview_marmoset_yolo_track.multview_coupleball_refine $vfile.matpkl $vfile.calibpkl --pod_len 0.5

# 6. 合成小球3D轨迹，并绘制3D轨迹视频
python -m lilab.multiview_scripts_dev.s4_matpkl2matcalibpkl $vfile.matpkl $vfile.calibpkl

# python -m lilabnext.multview_marmoset_track.s5_show_calibpkl2video $vfile.matcalibpkl
python -m lilab.multiview_scripts_dev.s5_show_calibpkl2video $vfile.matcalibpkl --axis-length 0 --only3D


# 8. [可选项] 以最后一个相机作为怼脸相机，设置align 坐标系
python -m lilabnext.multview_marmoset_track.a0_calibpkl_align_cam $vfile.calibpkl

python -m lilab.multiview_scripts_dev.s4_matpkl2matcalibpkl $vfile.matpkl $vfile.aligncalibpkl
python -m lilab.multiview_scripts_dev.s5_show_calibpkl2video --axis-length 0 $vfile.matcalibpkl 

# 9. [可选择] 对应 2K 相机的坐标系
python -m lilabnext.multview_marmoset_track.a0b_calibpkl_rescale_mkv $vfile.aligncalibpkl
#查询相机初始位置 (pan=985, tilt=215, zoom=11)
