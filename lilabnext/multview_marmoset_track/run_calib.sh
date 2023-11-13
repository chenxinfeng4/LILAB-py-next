#%% 1. 从头开始，矫正内参
# intrin1.mp4 2.mp4 3.mp4
project_ball_calib=/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/
cd $project_ball_calib

ls intrin*.mp4 | xargs -n 1 python -m lilab.cvutils_new.extract_frames --npick 100

mkdir -p intrinsic_calib_frames/{0,1,2}
mv outframes/intrin1*.jpg intrinsic_calib_frames/0
mv outframes/intrin2*.jpg intrinsic_calib_frames/1
mv outframes/intrin3*.jpg intrinsic_calib_frames/2
rm -r outframes

python -m lilabnext.multview_marmoset_track.intrinsic_utils intrinsic_calib_frames/ --board_size 11 8
#'将内参的 intrinsic_calib_frames/intrinsics_calib.json 拷贝到 lilab/cameras_setup/_get_calibinfo.py'

#%% 2A. 从头开始，视频抽帧，打标
# f1.mp4 2.mp4 3.mp4
ls f*.mp4 | xargs -n 1 python -m lilab.cvutils_new.extract_frames --npick 100
mv outframes/ ball_frames/

rm `comm -3 <(ls -1 ball_frames/*.jpg | sort) <(ls -1 ball_frames/*.json | sed s/json/jpg/ | sort)`
project_nake_name=ball_640x480_20231113_marmosetcam
mv ball_frames $project_nake_name
python -m lilab.cvutils.labelme_to_cocokeypoints_ball $project_nake_name
python -m lilab.cvutils.coco_split -s 0.9 ${project_nake_name}_trainval.json
cp -r ${project_nake_name}* /home/liying_lab/chenxinfeng/DATA/mmpose/data/ball/

# 添加新的数据到里面

mfile='res50_coco_ball_640x480.py'
mfile_nake=${mfile%.*}

cd /home/liying_lab/chenxinfeng/DATA/mmpose
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

#%% 2B. 外参矫正
cd $project_ball_calib
vfile=f1
python -m lilabnext.multview_marmoset_track.s1_ballvideo2matpkl_full_faster \
    --pannels 3 --config /home/liying_lab/chenxinfeng/DATA/mmpose/$mfile  $vfile.mp4

python -m lilabnext.multview_marmoset_track.s5_show_calibpkl2video f1.matpkl
setupname=david
python -m lilabnext.multiview_zyy.p1_checkboard_global global1.mp4 --setupname $setupname --board_size 11 8 --square_size 20 &

tball=" 0 0 0 0 10 " # 没有用，只是占位
python -m lilabnext.multiview_zyy.s2_matpkl2ballpkl $vfile.matpkl  --time  $tball --force-setupname  $setupname

