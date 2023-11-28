# pyinstaller qt5_window2x2_monitor.py
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QGridLayout, 
                             QWidget, QVBoxLayout, QSizePolicy, QSpacerItem,
                             QToolBar, QAction, QMenuBar)
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
import threading
import ffmpegcv
import datetime
import time
import socket
import numpy as np
from functools import partial


is_recording = False
is_realtime_com2d = False
is_realtime_com3d = False
# rt_server_ip = '10.50.60.6'
rt_server_ip = '10.50.5.83'
rt_server_port = 8090

caps = ['rtsp://admin:2019Cibr@10.50.5.252:8091/Streaming/Channels/102',
        'rtsp://admin:2019Cibr@10.50.5.252:8092/Streaming/Channels/102',
        'rtsp://admin:2019Cibr@10.50.5.252:8093/Streaming/Channels/102',
        'rtsp://admin:2019Cibr@10.50.5.252:8080/Streaming/Channels/102']

frames = [None for i in range(len(caps))]
frames_lock = [threading.Lock() for i in range(len(caps))]
camsize_wh = (640, 480)
labels = []

app = QApplication([])
window = QMainWindow()
window.setWindowTitle("视频播放")

def send_read(tcp_socket:socket.socket, send_data:str):
    send_data_byte = send_data.encode("utf-8")
    tcp_socket.send(send_data_byte)
    from_server_msg = tcp_socket.recv(1024)
    return from_server_msg.decode("utf-8")


def my_thread_recording(choose_cam_ids:list):
    time_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_files = [f'{time_str}_cam{i+1}.mp4' for i in range(len(caps)) if i in choose_cam_ids]
    vid_out_list = [ffmpegcv.VideoWriter(out_file, pix_fmt='rgb24', fps=25) for out_file in out_files]
    time_start = time.time()
    interval = 1/25
    while is_recording:
        frames_ = [frames[i] for i in range(len(caps)) if i in choose_cam_ids]
        for vid_out, frame in zip(vid_out_list, frames_):
            vid_out.write(frame)
        sleep_t = interval - (time.time() - time_start)
        time.sleep(max(0, sleep_t))
        time_start += interval
        
    for vid_out in vid_out_list:
        vid_out.release()
    print("录制结束")


def record_all():
    global is_recording
    if is_recording:
        return
    else:
        is_recording = True
        print("录制所有被点击")
        my_thread = threading.Thread(target=my_thread_recording, args=(list(range(len(caps))),))
        my_thread.start()

def record_which(i: int):
    global is_recording
    if is_recording:
        return
    else:
        is_recording = True
        my_thread = threading.Thread(target=my_thread_recording, args=([i-1],))
        my_thread.start()
        print(f"录制{i}被点击")



def stop():
    global is_recording
    if is_recording:
        print("停止被点击")
        is_recording = False

class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.anno_box_wh = 10
        self.painter = QPainter(parent)
        self.point = (0,0)
        self.point_ba = (0,0)
    
    def update_point(self, x, y, xba, yba):
        self.point = (x, y)
        self.point_ba = (xba, yba)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        w = h = int(self.anno_box_wh)
        self.painter.begin(self) # 开始绘制
        if is_realtime_com2d:
            self.painter.setPen(QPen(Qt.red, 2)) # 设置绘图的颜色和线宽
            x, y = np.array(self.point).astype(int) - int(w//2)
            self.painter.drawRect(x, y, w, h) # 绘制方框
        if is_realtime_com3d:
            self.painter.setPen(QPen(Qt.green,2))
            xba, yba = np.array(self.point_ba).astype(int) - int(w//2)
            self.painter.drawEllipse(xba, yba, w, h) # 绘制圆
        self.painter.end()  # 结束绘制

class My_Thread_realtime_com2d(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.send_data = 'com2d'
        self.send_data_ba = 'com2d_ba'

    def run(self):
        thr = 0.4
        fps = 25
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((rt_server_ip, rt_server_port))
        print('ready print')
        while is_realtime_com2d:
            time.sleep(1/fps)
            result = send_read(tcp_socket, self.send_data)
            if not len(result): continue
            iframe, *xypoints = [float(f) for f in result.strip().split(',')]
            points_n_xyp = np.array(xypoints).reshape(-1, 3)
            if is_realtime_com3d:
                result_ba = send_read(tcp_socket, self.send_data_ba)
                iframe, *xypoints_ba = [float(f) for f in result_ba.strip().split(',')]
                points_n_xyp_ba = np.array(xypoints_ba).reshape(-1, 3)
            else:
                points_n_xyp_ba = points_n_xyp*0
            for label, (x,y,p), (x2,y2,p2) in zip(labels, points_n_xyp, points_n_xyp_ba):
                if p<=thr and p2<=thr: continue
                label.update_point(x, y, x2, y2)
        tcp_socket.close()


def realtime_com2d():
    global is_realtime_com2d
    if is_realtime_com2d:
        return
    else:
        is_realtime_com2d = True
        print("实时比对被点击")
        my_thread = My_Thread_realtime_com2d(window)
        threading.Thread(target=my_thread.start).start()

def realtime_com3d():
    global is_realtime_com3d
    if is_realtime_com3d:
        return
    else:
        is_realtime_com3d = True

def realtime_stop():
    global is_realtime_com2d
    global is_realtime_com3d
    is_realtime_com2d = False
    is_realtime_com3d = False


# 创建主窗口和布局
central_widget = QWidget(window)
toolbar_layout = QVBoxLayout(central_widget)

def create_menu():
    # 创建菜单栏
    menu_bar = QMenuBar()
    window.setMenuBar(menu_bar)

    # 创建菜单
    menu_record = menu_bar.addMenu("录制")
    menu_status= menu_bar.addMenu("<已停止录制>")

    def record_status_trigger_changed():
        newStr = '<录制中>' if is_recording else '<已停止录制>'
        menu_status.setTitle(newStr)

    # 创建菜单项并绑定回调函数
    action_record_all = QAction('录制所有', window)
    action_record_all.triggered.connect(record_all)
    menu_record.addAction(action_record_all)

    for i in range(len(caps)):
        action_record_i = QAction('录制' + str(i + 1), window)
        action_record_i.triggered.connect(partial(record_which, i))
        menu_record.addAction(action_record_i)

    action_stop = QAction('停止', window)
    action_stop.triggered.connect(stop)
    menu_record.addAction(action_stop)

    for action in menu_record.actions():
        action.triggered.connect(record_status_trigger_changed)

    # 创建 realtime com2d, com3d 反馈
    menu_realtime = menu_bar.addMenu("实时反馈")
    action_realtime_com2d = QAction('com2d', window)
    action_realtime_com2d.triggered.connect(realtime_com2d)
    menu_realtime.addAction(action_realtime_com2d)

    action_realtime_com3d = QAction('com3d', window)
    action_realtime_com3d.triggered.connect(realtime_com3d)
    menu_realtime.addAction(action_realtime_com3d)

    action_realtime_com3d = QAction('停止', window)
    action_realtime_com3d.triggered.connect(realtime_stop)
    menu_realtime.addAction(action_realtime_com3d)


# 创建一个网格布局和一个主窗口
layout = QGridLayout()
widget = QWidget()
window.setCentralWidget(widget)
widget.setLayout(layout)
create_menu()
window.show()

# 创建4个QLabel控件用于显示视频帧
for i in range(2):
    for j in range(2):
        label = ImageLabel(window)
        layout.addWidget(label, i+1, j)
        labels.append(label)
        label.setScaledContents(True)

layout.setColumnStretch(0, 1)
layout.setColumnStretch(1, 1)
layout.setRowStretch(0, 1)
layout.setRowStretch(1, 1)
layout.addLayout(toolbar_layout, 0, 0, 1, layout.columnCount())

class VideoThread(QThread):
    frame_ready = pyqtSignal(object)  # 定义帧就绪信号

    def __init__(self, ipannel, video_path):
        super().__init__()
        self.video_path = video_path
        self.ipannel = ipannel
    def run(self):
        cap = ffmpegcv.VideoCaptureStreamRT(self.video_path, 
                                            camsize_wh=camsize_wh,
                                            pix_fmt='rgb24')
        while True:
            ret, frame = cap.read()
            with frames_lock[self.ipannel]:
                frames[self.ipannel] = frame
            if not ret:
                break
            # 更新图像数据
            image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            self.frame_ready.emit(pixmap)  # 发送帧就绪信号

        cap.release()

def display_frame(i, pixmap):
    labels[i].setPixmap(pixmap)

# 创建视频线程并连接帧就绪信号与显示函数
# caps = [r"F:\rec-1-CXF-20230219165121-camera-0.avi", r"F:\rec-1-CXF-20230219165121-camera-0.avi",
#         r"F:\rec-1-CXF-20230219165121-camera-0.avi", r"F:\rec-1-CXF-20230219165121-camera-0.avi"]

threads = []
for ipannel, cap in enumerate(caps):
    print(ipannel, cap, labels[ipannel])
    video_thread = VideoThread(ipannel, cap)
    video_thread.frame_ready.connect(lambda x,ip=ipannel:display_frame(ip, x))
    threads.append(video_thread)

for video_thread in threads:
    video_thread.start()  # 启动视频线程
# video_thread = VideoThread(r"F:\rec-1-CXF-20230219165121-camera-0.avi")
# video_thread.frame_ready.connect(display_frame)

# video_thread.start()  # 启动视频线程

app.exec_()