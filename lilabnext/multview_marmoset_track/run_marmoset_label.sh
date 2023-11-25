#%% 2A. 从头开始，视频抽帧，打标
# f1.mp4 2.mp4 3.mp4
project_ball_calib=/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2023-11-15-calib
cd $project_ball_calib
marmoset_video='2023-11-15_18-53-05_cam'

ls $marmoset_video*.mp4 | xargs -n 1 python -m lilab.cvutils_new.extract_frames --npick 100
mv outframes/ ball_frames/

# 用 labelme 打标，结束后执行下面
rm `comm -3 <(ls -1 ball_frames/*.jpg | sort) <(ls -1 ball_frames/*.json | sed s/json/jpg/ | sort)`
project_nake_name=toy_640x480_20231115_marmosetcam
mv ball_frames $project_nake_name
python -m lilab.cvutils.labelme_to_cocokeypoints_ball $project_nake_name
python -m lilab.cvutils.coco_split -s 0.9 ${project_nake_name}_trainval.json
cp -r ${project_nake_name}* /home/liying_lab/chenxinfeng/DATA/mmpose/data/toy/

# 添加新的数据到里面
cd /home/liying_lab/chenxinfeng/DATA/mmpose
mfile='res50_coco_toy_640x480.py'
mfile_nake=${mfile%.*}


vim $mfile

# 开始训练
python tools/train.py $mfile

# 模型文件转化为 onnx， tensorrt。提升推断速度
python -m lilab.mmpose_dev.a2_convert_mmpose2onnx $mfile --full --dynamic
trtexec --onnx=work_dirs/${mfile_nake}/latest.full.onnx \
    --fp16 --saveEngine=work_dirs/${mfile_nake}/latest.full.engine \
    --timingCacheFile=work_dirs/${mfile_nake}/.cache.txt \
    --workspace=3072 --optShapes=input_1:4x3x480x640 \
    --minShapes=input_1:1x3x480x640 --maxShapes=input_1:6x3x480x640

#%% 深度学习预测 toy 位置
setupname=david
config='/home/liying_lab/chenxinfeng/DATA/mmpose/res50_coco_toy_640x480.py'
vfile=`w2l "\\liying.cibr.ac.cn\Data_Temp\Chenxinfeng\marmoset_camera3_cxf\2023-11-15-calib\2023-11-15_18-50-34_cam1"`
# python -m lilabnext.multiview_zyy.s1_ballvideo2matpkl_full_faster $vfile.mp4 --pannels $setupname --config  $config #<深度学习>


python -m lilabnext.multview_marmoset_track.s1_ballvideo2matpkl_full_faster \
    --pannels 3 --config /home/liying_lab/chenxinfeng/DATA/mmpose/$mfile  $vfile.mp4

python -m lilabnext.multview_marmoset_track.s5_show_calibpkl2video $vfile.matpkl

calibpkl=/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2023-11-15-calib/ball_move_cam1.calibpkl
python -m lilab.multiview_scripts_dev.s4_matpkl2matcalibpkl $vfile.matpkl $calibpkl
python -m lilabnext.multview_marmoset_track.s5_show_calibpkl2video $vfile.matcalibpkl
