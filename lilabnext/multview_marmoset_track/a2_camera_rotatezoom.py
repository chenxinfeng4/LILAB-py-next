# python -m lilabnext.multview_marmoset_track.a2_camera_rotatezoom
import numpy as np
from lilabnext.multview_marmoset_track.a1_ptz_control import control as ptz_control
import time
import socket
import argparse


ptz_ip_port = ('10.50.4.130', '7094')
baseline_ptz = (985,215,11)

def PtzControl(ip:str, port:str, baseline_ptz:list):
    basePan, baseTilt, baseZoom = baseline_ptz
    phi_angle = basePan / 10 *np.pi / 180     #Pan:=phi
    theta_angle = baseTilt / 10 *np.pi / 180  #tilt:=theta
    Xi = [np.cos(phi_angle), 0, -np.sin(phi_angle)] #(u,v,w)
    Yi = [-np.sin(theta_angle)*np.sin(phi_angle), np.cos(theta_angle), -np.sin(theta_angle)*np.cos(phi_angle)]
    Zi = [np.cos(theta_angle)*np.sin(phi_angle), np.sin(theta_angle), np.cos(theta_angle)*np.cos(phi_angle)]
    R = np.array([Xi, Yi, Zi]).T  
    camera_s = np.array(baseline_ptz, dtype=int)
    lazy_count = 0
    yes_count = 0

    def inner(object_p: np.ndarray):
        nonlocal lazy_count, yes_count
        object_p = np.array(object_p, dtype=float).reshape(3,1)
        object_p_registed = np.dot(R, object_p).squeeze()

        # 计算相机与物体之间的相对位置
        relativePosition = object_p_registed

        # 计算相机需要调整的俯仰和倾斜角度
        targetPan = np.rad2deg(np.arctan2(relativePosition[0], relativePosition[2]))
        targetPan = (targetPan + 360)%360
        targetTilt = np.rad2deg(np.arcsin(relativePosition[1] / np.linalg.norm(relativePosition)))
        targetZoom = 29

        # 更新相机参数
        currentPan, currentTilt, currentZoom = camera_s
        pan_s = (abs(targetPan - currentPan / 10) > 5 and abs(targetPan - currentPan / 10) < 355)
        tilt_s = abs(currentTilt / 10 - targetTilt) > 5
        z_s = abs(targetZoom - currentZoom) > 5

        if pan_s or tilt_s or z_s: #位置发生了改变
            camera_s[:] = round(targetPan * 10), max(0, round(targetTilt * 10)), np.clip(10, 60, targetZoom)
            ptz_control(*camera_s, ip=ip, port=port)
            print(f'Do something...{yes_count}, {pan_s}, {tilt_s}, {z_s} P...{targetPan}, T {targetTilt}')
            yes_count = (yes_count + 1)%100 

    return inner


def send_read(tcp_socket, send_data='com3d'):
    send_data_byte = send_data.encode("utf-8")
    tcp_socket.send(send_data_byte)
    from_server_msg = tcp_socket.recv(1024)
    return from_server_msg.decode("utf-8")


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server-ip-port', type=str, default='localhost:8090')
    parser.add_argument('--ptz-ip-port', type=str, default=':'.join(ptz_ip_port))
    parser.add_argument('--baseline-ptz', type=str, default='985,215,11')
    args = parser.parse_args()
    serve_ip, serve_port = args.server_ip_port.split(':')
    ptz_ip, ptz_port = args.ptz_ip_port.split(':')
    baseline_ptz = [int(n) for n in args.baseline_ptz.split(',')]

    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((serve_ip, int(serve_port)))
    ptzControler = PtzControl(ip=ptz_ip, port=ptz_port, baseline_ptz=baseline_ptz)
    
    while True:
        response = send_read(tcp_socket)
        iframe, *p3d = [float(i) for i in response.split('\t')[-1].split(',')]
        p3d = np.array(p3d)
        axis_r = np.array([1,1,1], dtype=float)  #[-1,-1,1]
        object_p = p3d*axis_r
        camera_s = ptzControler(object_p)
        time.sleep(0.02)
