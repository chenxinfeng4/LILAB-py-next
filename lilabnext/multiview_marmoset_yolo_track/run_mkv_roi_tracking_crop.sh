cd /mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-1-31_sync/ballmove
vfile_mp4=2024-01-31_13-47-48.mp4
vfile=${vfile_mp4%.*}
calibpkl='ball_move_cam1.mkv.calibpkl'

python -m lilabnext.multiview_marmoset_yolo_track.a1_mkvvideos2matpkl $vfile.mp4
python -m lilab.multiview_scripts_dev.s4_matpkl2matcalibpkl $vfile.mkv.matpkl $calibpkl
python -m lilabnext.multiview_marmoset_yolo_track.a2_matcalibpkl2roitrackpkl $vfile.mkv.matcalibpkl
python -m lilabnext.multiview_marmoset_yolo_track.a3_roi_pick $vfile.mp4 $vfile.mkv.matcalibpkl

