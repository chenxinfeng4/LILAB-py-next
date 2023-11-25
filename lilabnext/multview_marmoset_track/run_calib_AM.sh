#%% 1. 从头开始，矫正内参
# intrin1.mp4 2.mp4 3.mp4
project_ball_calib=/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2023-11-22-calib
cd $project_ball_calib

ls checkboard_move*.mp4 | xargs -n 1 python -m lilab.cvutils_new.extract_frames --npick 100

mkdir -p intrinsic_calib_frames/{0,1,2}
mv outframes/checkboard_move_cam1*.jpg intrinsic_calib_frames/0
mv outframes/checkboard_move_cam2*.jpg intrinsic_calib_frames/1
mv outframes/checkboard_move_cam3*.jpg intrinsic_calib_frames/2
rm -r outframes

python -m lilabnext.multview_marmoset_track.intrinsic_utils intrinsic_calib_frames/ --board_size 11 8
#'将内参的 intrinsic_calib_frames/intrinsics_calib.json 拷贝到 lilab/cameras_setup/_get_calibinfo.py'

#%% 2A. 从头开始，视频抽帧，打标
# f1.mp4 2.mp4 3.mp4
ls ball_move_cam*.mp4 | xargs -n 1 python -m lilab.cvutils_new.extract_frames --npick 100
mv outframes/ ball_frames/

#打开LABELME 打标小球，Open Dir，选择ball_640x480_20231124_marmosetcam文件夹，右键create point...全部结束后直接关闭，改下面ball_640x480_20231124日期， 执行
rm `comm -3 <(ls -1 ball_frames/*.jpg | sort) <(ls -1 ball_frames/*.json | sed s/json/jpg/ | sort)`
project_nake_name=ball_640x480_20231124_marmosetcam
mv ball_frames $project_nake_name
python -m lilab.cvutils.labelme_to_cocokeypoints_ball $project_nake_name
python -m lilab.cvutils.coco_split -s 0.9 ${project_nake_name}_trainval.json
cp -r ${project_nake_name}* /home/liying_lab/chenxinfeng/DATA/mmpose/data/ball/

# 添加新的数据到里面

mfile='res50_coco_ball_640x480.py'
mfile_nake=${mfile%.*}

cd /home/liying_lab/chenxinfeng/DATA/mmpose
echo $mfile   #然后 ctrl + 鼠标左键，进入res50_coco_ball_640x480.py， 在140多行复制新的dict, 日期改为上面一样
# vim $mfile

# 开始训练
conda activate mmpose
python tools/train.py $mfile

# 模型文件转化为 onnx， tensorrt。提升推断速度
python -m lilab.mmpose_dev.a2_convert_mmpose2onnx $mfile --full --dynamic
conda activate mmdet
trtexec --onnx=work_dirs/${mfile_nake}/latest.full.onnx \
    --fp16 --saveEngine=work_dirs/${mfile_nake}/latest.full.engine \
    --timingCacheFile=work_dirs/${mfile_nake}/.cache.txt \
    --workspace=3072 --optShapes=input_1:4x3x480x640 \
    --minShapes=input_1:1x3x480x640 --maxShapes=input_1:6x3x480x640

#%% 2B. 外参矫正 确认文件名
cd $project_ball_calib
vfile=ball_move_cam1
mfile='res50_coco_ball_640x480.py'
vfile_checkboard='checkboard_global2_cam1'
python -m lilabnext.multview_marmoset_track.s1_ballvideo2matpkl_full_faster \
    --pannels 3 --config /home/liying_lab/chenxinfeng/DATA/mmpose/$mfile  $vfile.mp4

python -m lilabnext.multview_marmoset_track.s5_show_calibpkl2video $vfile.matpkl
setupname=david
python -m lilabnext.multiview_zyy.p1_checkboard_global $vfile_checkboard.mp4 --setupname $setupname --board_size 11 8 --square_size 20

tball=" 0 0 0 0 10 " # 没有用，只是占位
python -m lilabnext.multiview_zyy.s2_matpkl2ballpkl $vfile.matpkl  --time  $tball --force-setupname  $setupname

python -m lilab.multiview_scripts_dev.s3_ballpkl2calibpkl $vfile.ballpkl --skip-camera-intrinsic --skip-global 
python -m lilab.multiview_scripts_dev.p2_calibpkl_refine_byglobal $vfile.calibpkl $vfile_checkboard.globalrefpkl

# 6. 合成小球3D轨迹，并绘制3D轨迹视频
python -m lilab.multiview_scripts_dev.s4_matpkl2matcalibpkl $vfile.matpkl $vfile.recalibpkl

python -m lilabnext.multview_marmoset_track.s5_show_calibpkl2video $vfile.matcalibpkl

# 7. 确定无误后，替换原来的 calibpkl
mv $vfile.recalibpkl $vfile.calibpkl