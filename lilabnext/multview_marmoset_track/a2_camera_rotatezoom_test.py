import numpy as np
from lilabnext.multview_marmoset_track.a1_ptz_control import control as ptz_control
import lilabnext.multview_marmoset_track.a1_ptz_control as ptz_cam
import time
import socket
from multiview_calib.calibpkl_predict import CalibPredict
from scipy.interpolate import interp1d
import tqdm

tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# serve_ip = '10.50.5.83'
serve_ip = '127.0.0.1'
serve_port = 8090
ptz_cam.ip = '192.168.1.50'
ptz_cam.port = 80

tcp_socket.connect((serve_ip, serve_port))
calibpkl = '/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2023-11-27-calib/ball_move_cam1.aligncalibpkl'
calibpkl = '/home/chenxinfeng/ml-project/LILAB-pynext/lilabnext/multview_marmoset_track/ball_move_cam1.aligncalibpkl'

def get_zoom(offset=10, range=[10, 40]):
    calib = CalibPredict(calibpkl)
    calib.image_shape = None
    xtick = [0.1, 0.2, 0.5, 1, 1.3, 1.5, 1.7, 2, 2.2, 2.5, 4, 5, 6]
    xlen = []
    for x in xtick:
        p3d = [[0, 0, x],
                [0.29, 0, x]]
        p3d = np.array(p3d, dtype=np.float64)
        p2d = calib.p3d_to_p2d(p3d)[-1]
        xlen.append(np.linalg.norm(p2d[0]-p2d[1]))
    xtick = np.array(xtick)
    xlen = np.array(xlen)
    f = interp1d(xtick, xlen, kind='linear')
    
    def get_zoom_param(xyz_dist):
        pixellen_now = f(xyz_dist)
        zoom_factor = 100/pixellen_now
        zoom_param_diff = zoom_factor / 2.7 * 30
        zoom_param = np.clip(zoom_param_diff + offset, range[0], range[1])
        zoom_param = int(zoom_param)
        return zoom_param
    return get_zoom_param

lazy = 0
get_zoom_param = get_zoom(offset=15, range=[10, 40])
camera_s=[0,0,10]
def camera_rotation1(object_p, camera_s=[0,0,10]):
    # 物体的三维坐标 (objectX, objectY, objectZ)
    object_p = np.array(object_p, dtype=float)
    camera_s = np.array(camera_s, dtype=int)

    # PTZ相机的三维坐标 (cameraX, cameraY, cameraZ)
    camera_pos_XYZ = np.zeros(3, dtype=float)
    # 获取相机当前状态（旋转、俯仰、缩放等参数）
    currentPan, currentTilt, currentZoom = camera_s

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
    # k_cxf = 4
    # targetZoom = 20 * round(np.linalg.norm(relativePosition*k_cxf), -1)
    targetZoom = get_zoom_param(np.linalg.norm(relativePosition))

    # 更新相机参数
    pan_s = (abs(targetPan - currentPan / 10) > 5 and abs(targetPan - currentPan / 10) < 355)
    tilt_s = abs(currentTilt / 10 - targetTilt) > 5
    z_s = abs(targetZoom - currentZoom) > 2

    global lazy

    if pan_s or tilt_s or z_s:
        if lazy>0:
            lazy -= 1
        else:
            print(pan_s, tilt_s, z_s, f'CurrentZoom{currentZoom} targetZoom {targetZoom} ')
            camera_s[:] = round(targetPan * 10),max(0, round(targetTilt * 10)), max(10, targetZoom)
            lazy = 15
            ptz_control(*camera_s)

    return camera_s


def send_read(send_data='com3d'):
    send_data_byte = send_data.encode("utf-8")
    tcp_socket.send(send_data_byte)
    from_server_msg = tcp_socket.recv(1024)
    return from_server_msg.decode("utf-8")


bar = tqdm.tqdm(desc='PTZ control')
while True:
    bar.update(1)
    response = send_read()
    iframe, *p3d = [float(i) for i in response.split('\t')[-1].split(',')]
    p3d = np.array(p3d)
    axis_r = np.array([-1,-1,1], dtype=float)
    object_p = p3d*axis_r
    camera_s = camera_rotation1(object_p, camera_s)
    time.sleep(0.038)
