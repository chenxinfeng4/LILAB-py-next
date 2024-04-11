source activate mmdet


# ==================== wsl ================
checkpoint=/root/ml-project/syncdata/yolov8n_det_640_ballrg.singleton.engine; ijoint=0
checkpoint=/root/ml-project/syncdata/yolov8n_det_640_marmoset.singleton.engine; ijoint=1

calibpkl=/root/ml-project/syncdata/ball_move.aligncalibpkl
zfmappkl=/root/ml-project/syncdata/focus_length.zfmappkl

server_creategport=8090
server_ip_port=localhost:8090
ptz_ip_port=192.168.1.210:80
baseline_ptz=267.47,60.76,1.0

python -m lilabnext.multiview_marmoset_yolo_track.t1_realtime_position \
    --checkpoint $checkpoint --calibpkl $calibpkl --createport $server_creategport --ijoint $ijoint

python -m lilabnext.multiview_marmoset_yolo_track.t2_point3d_set_ptzf \
    --server-ip-port $server_ip_port --ptz-ip-port $ptz_ip_port \
    --baseline-ptz $baseline_ptz --zfmappkl $zfmappkl

