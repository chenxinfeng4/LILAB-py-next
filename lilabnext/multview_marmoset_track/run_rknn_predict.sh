#%%
cd /home/chenxinfeng/ml-project/rknn_mmpose/
sudo -E su -p 
conda activate rknn
# python t1_realtime_position_partmerge.py --checkpoint mobilenetv3_ball_640x480.rknn --calibpkl ball_move_cam1.calibpkl > /dev/null
python t1_realtime_position_partmerge.py --checkpoint mobilenetv3_ball_640x480.rknn --calibpkl /home/chenxinfeng/ml-project/LILAB-pynext/lilabnext/multview_marmoset_track/ball_move_cam1.aligncalibpkl > /dev/null

#%%


#%%
conda activate rknn
python /home/chenxinfeng/ml-project/LILAB-pynext/lilabnext/multview_marmoset_track/a2_camera_rotatezoom_test.py

#%%
python D:\ml-project\LILAB-pynext\lilabnext\multview_marmoset_track\qt5_window2x2_monitor.py