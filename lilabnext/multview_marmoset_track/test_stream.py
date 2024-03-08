# %%
import numpy as np
import ffmpegcv
from ffmpegcv.ffmpeg_noblock import ReadLiveLast
import cv2
import tqdm
import socket
# rtsp://admin:2019Cibr@192.168.1.61:554/Streaming/Channels/102

rtsp_streams = [
                'rtsp://admin:2019Cibr@192.168.1.61:554/Streaming/Channels/102',
                'rtsp://admin:2019Cibr@192.168.1.62:554/Streaming/Channels/102',
                'rtsp://admin:2019Cibr@192.168.1.63:554/Streaming/Channels/102',
                'rtsp://admin:2019Cibr@192.168.1.50:554/Streaming/Channels/102'
                ]
video_file1, video_file2, video_file3, video_file4 = rtsp_streams

rt_server_ip = '10.50.4.182'
rt_server_port = 8090
show_3d = True


def send_read(tcp_socket:socket.socket, send_data:str):
    send_data_byte = send_data.encode("utf-8")
    tcp_socket.send(send_data_byte)
    from_server_msg = tcp_socket.recv(1024)
    return from_server_msg.decode("utf-8")
send_data = 'com2d'
send_data_ba = 'com2d_ba'
thr = 0.4
fps = 25
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_socket.connect((rt_server_ip, rt_server_port))

vid1 = ffmpegcv.VideoCaptureStreamRT(video_file1, 
                    camsize_wh=(640,480), pix_fmt='bgr24')
vid2 = ReadLiveLast(ffmpegcv.VideoCaptureStreamRT,video_file2, 
                    camsize_wh=(640,480), pix_fmt='bgr24')
vid3 = ReadLiveLast(ffmpegcv.VideoCaptureStreamRT,video_file3, 
                    camsize_wh=(640,480), pix_fmt='bgr24')
vid4 = ReadLiveLast(ffmpegcv.VideoCaptureStreamRT,video_file4, 
                    camsize_wh=(640,480), pix_fmt='bgr24')
ret1, frame1 = vid1.read()
print(frame1.shape)

def plot_a_frame(i, ret, frame, xyp, xyp_ba=None):
    if not ret: return
    (x, y, p) = xyp
    if ~np.isnan(x):
        cv2.rectangle(frame, (int(x-10), int(y-10)), (int(x+10), int(y+10)), (0,0,255), 2)
    if xyp_ba is not None and xyp_ba[-1]>=1:
        (x, y, p) = xyp_ba
        cv2.circle(frame, (int(x), int(y)), 10, (0,255,0), 2)
    cv2.imshow(f'frame{i}', frame)

a = tqdm.tqdm()
while True:
    a.update()
    ret1, frame1 = vid1.read()
    ret2, frame2 = vid2.read()
    ret3, frame3 = vid3.read()
    ret4, frame4 = vid4.read()
    result = send_read(tcp_socket, send_data)
    if not len(result): continue
    iframe, *xypoints = [float(f) for f in result.strip().split(',')]
    points_n_xyp = np.array(xypoints).reshape(-1, 3)
    
    if show_3d:
        result = send_read(tcp_socket, send_data_ba)
        _, *xypoints = [float(f) for f in result.strip().split(',')]
        points_n_xyp_ba = np.array(xypoints).reshape(-1, 3)
        result = send_read(tcp_socket, 'com3d')
        _, *xyzpoints = [float(f) for f in result.strip().split('\t')[1].split(',')]
        points_n_xyz = np.array(xyzpoints).reshape(-1, 3)[0]
    else:
        points_n_xyp_ba = [None]*len(points_n_xyp)
        points_n_xyz = [None, None, None]

    if show_3d and ~np.isnan(points_n_xyz[0]):
        text = ','.join([f'{v:6.2f}' for v in points_n_xyz])
        cv2.putText(frame1, text, (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)


    plot_a_frame(1,ret1, frame1, points_n_xyp[0], xyp_ba=points_n_xyp_ba[0])
    plot_a_frame(2, ret2, frame2, points_n_xyp[1], xyp_ba=points_n_xyp_ba[1])
    plot_a_frame(3, ret3, frame3, points_n_xyp[2], xyp_ba=points_n_xyp_ba[2])
    cv2.imshow('PTZ control', frame4)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
