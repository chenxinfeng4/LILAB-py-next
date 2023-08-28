#!/bin/bash
vfile_full=/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera6/20230824/ball_vid1_c.mp4
setupname=zyy  # ana bob carl, 3套多相机设备的标志
config="/home/liying_lab/chenxinfeng/DATA/mmpose/res50_coco_ball_512x512_ZYY.py"

# vfile=/mnt/liying.cibr.ac.cn_Data_Temp/multiview_9/chenxf/LZTxWT_230505/ball/2023-05-06_13-52-32Sball.mp4
# setupname="bob"  # ana bob carl, zyy, 4套多相机设备的标志

vfile=`echo "$vfile_full" | sed 's/.mp4//'`
vfile_checkboard_full=/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera6/20230824/checker_board_vid1.mp4
vfile_checkboard=`echo "$vfile_checkboard_full" | sed 's/.mp4//'`

tball=" 0 0 0 0 10 " # 没有用，只是占位

# 2A. 设置棋盘格，全局定标X、Y、Z轴
python -m lilabnext.multiview_zyy.p1_checkboard_global $vfile_checkboard.mp4 --setupname $setupname --board_size 11 8 --square_size 30 &

# 2B. 每个视角单独预测小球,绘制2D轨迹视频
python -m lilabnext.multiview_zyy.s1_ballvideo2matpkl_full_faster $vfile.mp4 --pannels $setupname --config  $config #<深度学习>

# python -m lilab.multiview_scripts_dev.s5_show_calibpkl2video $vfile.matpkl &


# 3. （可选）检查是否有坏点，修正 

# 4. 多相机 relative pose
python -m lilabnext.multiview_zyy.s2_matpkl2ballpkl $vfile.matpkl  --time  $tball --force-setupname  $setupname

python -m lilab.multiview_scripts_dev.s3_ballpkl2calibpkl $vfile.ballpkl --skip-camera-intrinsic --skip-global 

# 5. 用全局定标对齐，得到多相机 global pose
python -m lilab.multiview_scripts_dev.p2_calibpkl_refine_byglobal $vfile.calibpkl $vfile_checkboard.globalrefpkl

# 6. 合成小球3D轨迹，并绘制3D轨迹视频
python -m lilab.multiview_scripts_dev.s4_matpkl2matcalibpkl $vfile.matpkl $vfile.recalibpkl

python -m lilabnext.multiview_zyy.s5_show_calibpkl2video $vfile.matcalibpkl

# 7. 确定无误后，替换原来的 calibpkl
mv $vfile.recalibpkl $vfile.calibpkl

# 8. 导出为 matlab 格式，用于 label3D
python -m lilab.dannce.s1_ball2mat $vfile.calibpkl
