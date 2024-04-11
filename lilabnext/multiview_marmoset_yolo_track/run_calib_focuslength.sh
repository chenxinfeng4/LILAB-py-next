#%% 0. 【必须】 初始化
# intrin1.mp4 2.mp4 3.mp4
conda activate mmdet
project_dir=/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-4-10_Camera_calibration/Low/focal_length
cd $project_dir

nfocus=`ls [0-9].mp4 | wc -l`
for ((i=0; i<=$nfocus-1; i++)); do
    ffmpeg -i $((i+1)).mp4 -ss 00:00:00.000 -vframes 1 $((i+1)).png
done

# 用label3d 打标
# 修改文件，再运行
python -m lilabnext.multiview_calib.focus_length
