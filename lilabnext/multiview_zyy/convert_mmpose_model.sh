# ZYY project
mfile='res50_coco_ball_512x512_ZYY.py'

cd /home/liying_lab/chenxinfeng/DATA/mmpose
mfile_nake=${mfile%.*}

python -m lilab.mmpose_dev.a2_convert_mmpose2onnx $mfile --full --dynamic
trtexec --onnx=work_dirs/${mfile_nake}/latest.full.onnx \
    --fp16 --saveEngine=work_dirs/${mfile_nake}/latest.full.engine \
    --timingCacheFile=work_dirs/${mfile_nake}/.cache.txt \
    --workspace=3072 --optShapes=input_1:4x3x512x512 \
    --minShapes=input_1:1x3x512x512 --maxShapes=input_1:10x3x512x512
