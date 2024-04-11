# python -m lilabnext.multiview_marmoset_yolo_track.t2_point3d_set_ptzf
import numpy as np
from lilabnext.multview_marmoset_track.a1_ptz_control import control_PTZF as ptzf_control
from lilabnext.multiview_calib.focus_length import zf_interp_industry
import time
import socket
import argparse
import os.path as osp
import lilabnext.multiview_marmoset_yolo_track.t1a_realtime_position_daemon_rpc as sockserver


ptz_ip_port = ('10.50.4.130', '7094')
baseline_ptz = (267.47, 60.76, 1.0)
thr_move_x_y_z = np.array([0.12, 0.08, 0.1])
thr_move_xy = 0.15


def PtzControl(ip:str, port:str, baseline_ptz:list, zf_interp_fun:callable):
    basePan, baseTilt, baseZoom = baseline_ptz
    phi_angle = basePan *np.pi / 180     #Pan:=phi
    theta_angle = baseTilt *np.pi / 180  #tilt:=theta
    Xi = [np.cos(phi_angle), 0, -np.sin(phi_angle)] #(u,v,w)
    Yi = [-np.sin(theta_angle)*np.sin(phi_angle), np.cos(theta_angle), -np.sin(theta_angle)*np.cos(phi_angle)]
    Zi = [np.cos(theta_angle)*np.sin(phi_angle), np.sin(theta_angle), np.cos(theta_angle)*np.cos(phi_angle)]
    R = np.array([Xi, Yi, Zi]).T
    camera_s = np.zeros((4,), dtype=float)
    yes_count = 0
    object_p_r_last = np.array([0,0,0.5], dtype=float)
    

    def inner(object_p: np.ndarray):
        nonlocal yes_count, object_p_r_last
        object_p = np.array(object_p, dtype=float).reshape(3,1)

        # 物体位置对齐到PTZ轴
        relativePosition = np.dot(R, object_p).squeeze()

        # 计算物体移动的距离
        object_p_diff = np.abs(object_p_r_last - relativePosition)

        # 判断物体是否移动超过阈值
        object_p_diff_xy = np.linalg.norm(object_p_diff[:2])
        if np.any(object_p_diff < thr_move_x_y_z) and (object_p_diff_xy < thr_move_xy):
            return

        # 根据计算相机与物体之间的距离计算 zoom 和 focus
        dist_to_object = np.linalg.norm(relativePosition)
        targetZoom, targetFocus = zf_interp_fun(dist_to_object)

        # 计算相机需要调整的俯仰和倾斜角度
        targetPan = np.rad2deg(np.arctan2(relativePosition[0], relativePosition[2]))
        targetPan = (targetPan + 360)%360
        targetTilt = np.rad2deg(np.arcsin(relativePosition[1] / np.linalg.norm(relativePosition)))

        # 更新相机参数
        currentPan, currentTilt, currentZoom, currentFocus = camera_s
        pan_s = (abs(targetPan - currentPan) > 5 and abs(targetPan - currentPan) < 355)
        tilt_s = abs(currentTilt - targetTilt) > 5
        zoom_s = abs(targetZoom - currentZoom) > 0.5

        if pan_s or tilt_s or zoom_s: #位置发生了改变
            camera_s[:] = targetPan, max(0, targetTilt), targetZoom, targetFocus
            ptzf_control(*camera_s, ip=ip, port=port)
            print(f'Do something...{yes_count}, {pan_s}, {tilt_s}, {zoom_s} P...{targetPan}, T {targetTilt}')
            yes_count = (yes_count + 1)%100 

    return inner


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server-ip-port', type=str, default='localhost:8090')
    parser.add_argument('--ptz-ip-port', type=str, default=':'.join(ptz_ip_port))
    parser.add_argument('--baseline-ptz', type=str, default='267.47,60.76,1.0')
    parser.add_argument('--zfmappkl', type=str)
    args = parser.parse_args()
    serve_ip, serve_port = args.server_ip_port.split(':')
    ptz_ip, ptz_port = args.ptz_ip_port.split(':')
    baseline_ptz = [float(n) for n in args.baseline_ptz.split(',')]
    assert osp.exists(args.zfmappkl), 'zfmappkl not exists'
    zf_interp_fun = zf_interp_industry(args.zfmappkl)

    rpc_client = sockserver.create_client()
    ptzControler = PtzControl(ip=ptz_ip, port=ptz_port, 
                              baseline_ptz=baseline_ptz, zf_interp_fun=zf_interp_fun)
    
    while True:
        iframe, object_p = rpc_client.com3d()
        if False: #rotate_image_180
            axis_r = np.array([-1,-1,1], dtype=float)
            object_p = object_p * axis_r
        camera_s = ptzControler(object_p)
        time.sleep(0.02)
