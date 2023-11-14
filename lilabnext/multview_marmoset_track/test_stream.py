# %%
import numpy as np
import ffmpegcv
from ffmpegcv.ffmpeg_noblock import ReadLiveLast
import cv2
import tqdm
import socket
# rtsp://admin:2019Cibr@192.168.1.61:554/Streaming/Channels/102

# video_file1 = "rtsp://admin:Admin000@10.50.26.20:8081/CH002.sdp"
# video_file2 = "rtsp://admin:Admin000@10.50.26.20:8082/CH002.sdp"
# video_file3 = "rtsp://admin:Admin000@10.50.26.20:8083/CH002.sdp"

video_file1 = "rtsp://admin:2019Cibr@10.50.5.252:8091/Streaming/Channels/102"
video_file2 = "rtsp://admin:2019Cibr@10.50.5.252:8092/Streaming/Channels/102"
video_file3 = "rtsp://admin:2019Cibr@10.50.5.252:8093/Streaming/Channels/102"
rt_server_ip = '10.50.60.6'
rt_server_port = 8090

def send_read(tcp_socket:socket.socket, send_data:str):
    send_data_byte = send_data.encode("utf-8")
    tcp_socket.send(send_data_byte)
    from_server_msg = tcp_socket.recv(1024)
    return from_server_msg.decode("utf-8")
send_data = 'com2d'
thr = 0.4
fps = 25
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_socket.connect((rt_server_ip, rt_server_port))

# out_file1 = ffmpegcv.VideoWriter('global1.mp4')
# out_file2 = ffmpegcv.VideoWriter('global2.mp4')
# out_file3 = ffmpegcv.VideoWriter('global3.mp4')
vid1 = ffmpegcv.VideoCaptureStreamRT(video_file1, 
                    camsize_wh=(640,480), pix_fmt='bgr24')
vid2 = ReadLiveLast(ffmpegcv.VideoCaptureStreamRT,video_file2, 
                    camsize_wh=(640,480), pix_fmt='bgr24')
vid3 = ReadLiveLast(ffmpegcv.VideoCaptureStreamRT,video_file3, 
                    camsize_wh=(640,480), pix_fmt='bgr24')
ret1, frame1 = vid1.read()
cv2.imwrite('frame1.jpg', frame1)

print(frame1.shape)
a = tqdm.tqdm()
while True:
    a.update()
    ret1, frame1 = vid1.read()
    ret2, frame2 = vid2.read()
    ret3, frame3 = vid3.read()
    result = send_read(tcp_socket, send_data)
    if not len(result): continue
    iframe, *xypoints = [float(f) for f in result.strip().split(',')]
    points_n_xyp = np.array(xypoints).reshape(-1, 3)
    if ret1 == True:
        (x, y, p) = points_n_xyp[0]
        cv2.circle(frame1, (int(x), int(y)), 10, (0,255,0), 2)
        cv2.imshow('frame1', frame1)
    if ret2 == True:
        (x, y, p) = points_n_xyp[1]
        cv2.circle(frame2, (int(x), int(y)), 10, (0,255,0), 2)
        cv2.imshow('frame2', frame2)
    if ret3 == True:
        (x, y, p) = points_n_xyp[2]
        cv2.circle(frame3, (int(x), int(y)), 10, (0,255,0), 2)
        cv2.imshow('frame3', frame3)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

