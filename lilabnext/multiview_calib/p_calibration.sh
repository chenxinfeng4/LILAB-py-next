#!/bin/bash
# /home/liying_lab/chenxf/ml-project/LILAB-pynext/lilabnext/multiview_calib/p_calibration.sh VFILE SETUPNAME
if [ $# -lt 2 ]; then
    echo "缺少参数，请输入两个参数. 第一个为视频路径，第二个为设备名"
    exit 1
fi


vfilefull=$1
setupname=$2  # ana bob carl, 3套多相机设备的标志

vfile=`echo "$vfilefull" | sed 's/.mp4//'`
checkpoint=/home/liying_lab/chenxinfeng/DATA/ultralytics/work_dirs/yolov8n_det_640_ballrg/last.singleton.engine

python -m lilab.yolo_det.s1_video2matpkl --setupname $setupname --checkpoint $checkpoint $vfile.mp4 

# python -m lilab.multiview_scripts_dev.s5_show_calibpkl2video $vfile.matpkl


tball=" 0 0 0 0 10 " # 没有用，只是占位
# python -m lilabnext.multiview_zyy.s2_matpkl2ballpkl $vfile.matpkl  --time  $tball --force-setupname  $setupname
python -m lilab.multiview_scripts_dev.s2_matpkl2ballpkl $vfile.matpkl  --time  $tball --force-setupname  $setupname --nchoose 500
python -m lilab.multiview_scripts_dev.s3_ballpkl2calibpkl $vfile.ballpkl --skip-camera-intrinsic --skip-global 
python -m lilabnext.multiview_marmoset_yolo_track.multview_coupleball_refine $vfile.matpkl $vfile.calibpkl --pod_len 0.5

# 6. 合成小球3D轨迹
python -m lilab.multiview_scripts_dev.s4_matpkl2matcalibpkl $vfile.matpkl $vfile.calibpkl


# 7. [可选项] 以第一个PTZF相机作为怼脸相机，设置align 坐标系
python -m lilabnext.multiview_calib.a0_calibpkl_align_cam $vfile.calibpkl --iview-align 5

python -m lilab.multiview_scripts_dev.s4_matpkl2matcalibpkl $vfile.matpkl $vfile.aligncalibpkl
python -m lilab.yolo_det.s5_show_calibpkl2video $vfile.matcalibpkl 

mv $vfile.aligncalibpkl $vfile.calibpkl

# 8. [可选择] 对应 2K 相机的坐标系
python -m lilabnext.multiview_calib.a0b_calibpkl_rescale_mkv $vfile.calibpkl
