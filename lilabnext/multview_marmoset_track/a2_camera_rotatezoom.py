import numpy as np
from lilabnext.multview_marmoset_track.a1_ptz_control import control as ptz_control
import time
import socket


tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serve_ip = '10.50.5.83'
serve_port = 8090
tcp_socket.connect((serve_ip, serve_port))


def camera_rotation1(object_p, camera_s=[0,0,10]):
    # 物体的三维坐标 (objectX, objectY, objectZ)
    object_p = np.array(object_p, dtype=float)
    camera_s = np.array(camera_s, dtype=int)

    # PTZ相机的三维坐标 (cameraX, cameraY, cameraZ)
    camera_pos_XYZ = np.zeros(3, dtype=float)
    # 获取相机当前状态（旋转、俯仰、缩放等参数）
    currentPan = camera_s[0]
    currentTilt = camera_s[1]
    currentZoom = camera_s[2]

    # 计算相机与物体之间的相对位置
    relativePosition = object_p - camera_pos_XYZ

    # 计算相机需要调整的俯仰和倾斜角度
    if relativePosition[2] > 0:
        targetPan = 90 - np.arccos(relativePosition[0] / np.linalg.norm(relativePosition[[0, 2]])) * 180 / np.pi
        if targetPan < 0:
            targetPan = 360 + targetPan
    elif relativePosition[2] == 0 and relativePosition[0] > 0:
        targetPan = 90
    elif relativePosition[2] == 0 and relativePosition[0] < 0:
        targetPan = 270
    else:
        targetPan = 90 + np.arccos(relativePosition[0] / np.linalg.norm(relativePosition[[0, 2]])) * 180 / np.pi

    targetTilt = np.arcsin(relativePosition[1] / np.linalg.norm(relativePosition)) * 180 / np.pi

    # 计算物体与相机的距离并调整缩放参数
    k_cxf = 4
    targetZoom = 20 * round(np.linalg.norm(relativePosition*k_cxf), -1)

    # 更新相机参数
    pan_s = (abs(targetPan - currentPan / 10) > 5 and abs(targetPan - currentPan / 10) < 355)
    tilt_s = abs(currentTilt / 10 - targetTilt) > 5
    z_s = abs(targetZoom - currentZoom) > 5

    if pan_s or tilt_s or z_s:
        camera_s[0] = round(targetPan * 10)
        camera_s[1] = max(0, round(targetTilt * 10))
        camera_s[2] = max(10, targetZoom)
        ptz_control(*camera_s)

    return camera_s


def send_read(send_data='com3d'):
    send_data_byte = send_data.encode("utf-8")
    tcp_socket.send(send_data_byte)
    from_server_msg = tcp_socket.recv(1024)
    return from_server_msg.decode("utf-8")


while True:
    response = send_read()
    iframe, *p3d = [float(i) for i in response.split('\t')[-1].split(',')]
    p3d = np.array(p3d)
    axis_r = np.array([-1,-1,1], dtype=float)
    object_p = p3d*axis_r
    camera_s = camera_rotation1(object_p)
    time.sleep(0.04)