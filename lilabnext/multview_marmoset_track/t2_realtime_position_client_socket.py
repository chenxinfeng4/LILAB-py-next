#%% testsocket.py
import socket
import time
# %% create connection
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serve_ip = '10.50.60.6'
serve_port = 8090
tcp_socket.connect((serve_ip, serve_port))

def send_read(send_data):
    send_data_byte = send_data.encode("utf-8")
    tcp_socket.send(send_data_byte)

    from_server_msg = tcp_socket.recv(1024)
    print(from_server_msg.decode("utf-8"))
    return from_server_msg.decode("utf-8")
# %% Supported commands
cmds = ['hello', 'com3d', 'ba_poses', 'com2d', 'com2d_ba']

send_read('404') #warmup
a = time.time()
for send_data in cmds:
    send_read(send_data)
    dt = time.time() - a
    print(f'{send_data} took {dt} seconds')
    time.sleep(5)
    a = time.time() 

tcp_socket.close()