source activate mmdet


# ==================== wsl ================
checkpoint=/root/ml-project/syncdata/yolov8n_det_640_ballrg.singleton.engine; iclass=0
checkpoint=/root/ml-project/syncdata/yolov8n_det_640_marmoset.singleton.engine; iclass=1

calibpkl=/root/ml-project/syncdata/ball_move.aligncalibpkl
zfmappkl=/root/ml-project/syncdata/focus_length.zfmappkl

server_creategport=8090
server_ip_port=localhost:8090
ptz_ip_port=192.168.1.210:80
baseline_ptz=267.47,60.76,1.0

python -m lilabnext.multiview_marmoset_yolo_track.t1_realtime_position \
    --checkpoint $checkpoint --calibpkl $calibpkl --createport $server_creategport --iclass $iclass

python -m lilabnext.multiview_marmoset_yolo_track.t2_point3d_set_ptzf \
    --server-ip-port $server_ip_port --ptz-ip-port $ptz_ip_port \
    --baseline-ptz $baseline_ptz --zfmappkl $zfmappkl


# ==================== wsl multi_class================
checkpoint=/root/ml-project/syncdata/yolov8n_det_640_ballrg.singleton.engine
calibpkl=/root/ml-project/syncdata/ball_move.aligncalibpkl
zfmappkl=/root/ml-project/syncdata/focus_length.zfmappkl
server_ip_port=localhost:8090
server_creategport=8090

ptz_ip_port_list="192.168.1.210:80     192.168.1.211:80"
baseline_ptz_list="267.47,60.76,1.0    284.73,55.76,1.0"
iclass_list="0   0"

python -m lilabnext.multiview_marmoset_yolo_track.t1_realtime_position \
    --checkpoint $checkpoint --calibpkl $calibpkl --createport $server_creategport

python -m lilabnext.multiview_marmoset_yolo_track.t2_point3d_set_ptzf_multiclass \
    --server-ip-port $server_ip_port --zfmappkl $zfmappkl \
    --ptz-ip-port-list $ptz_ip_port_list \
    --baseline-ptz-list $baseline_ptz_list \
    --iclass-list $iclass_list


# ==================== wsl multi_instance================
checkpoint=/root/ml-project/syncdata/yolov8n_det_640_ballrg.singleton.engine; iclass=0
calibpkl=/root/ml-project/syncdata/ball_move.aligncalibpkl
zfmappkl=/root/ml-project/syncdata/focus_length.zfmappkl
server_ip_port=localhost:8090
server_creategport=8090

ptz_ip_port_list="192.168.1.210:80     192.168.1.211:80"
baseline_ptz_list="267.47,60.76,1.0    284.73,55.76,1.0"
iins_list="0   1"

ninstance=2

python -m lilabnext.multiview_marmoset_yolo_track.t1_realtime_position_multiins \
    --checkpoint $checkpoint --calibpkl $calibpkl --createport $server_creategport \
    --iclass $iclass --ninstance $ninstance

python -m lilabnext.multiview_marmoset_yolo_track.t2_point3d_set_ptzf_multiins \
    --server-ip-port $server_ip_port --zfmappkl $zfmappkl \
    --ptz-ip-port-list $ptz_ip_port_list \
    --baseline-ptz-list $baseline_ptz_list \
    --iins-list $iins_list

python -m lilabnext.multiview_marmoset_yolo_track.t2a_f2sync_ptzf_record