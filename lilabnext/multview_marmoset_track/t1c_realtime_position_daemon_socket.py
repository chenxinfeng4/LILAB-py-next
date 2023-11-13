# python -m lilabnext.multview_marmoset_track.t1c_realtime_position_daemon_socket

import socketserver
from .msg_file_io import read_msg, read_calibpkl_msg, read_com2d, read_com2d_ba

HOST, PORT = "127.0.0.1", 20169
HOST, PORT = "0.0.0.0", 8090

def greeting():
    msg = 'Welcome to the marmoset tracker!\n'
    return msg

def get_com3d():
    msg = read_msg()
    return msg

def get_com2d():
    return read_com2d()

def get_com2d_ba():
    return read_com2d_ba()

def get_ba_poses():
    msg = read_calibpkl_msg()
    return msg

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client

        print("conn is :",self.request) # conn
        print("addr is :",self.client_address) # addr
 
        try:
            while True:
                #收消息
                data = self.request.recv(1024)
                if not data:
                    self.request.sendall('\n'.encode('utf-8'))
                    break
                data = data.decode("utf-8").strip()
                # print("收到客户端的消息是", data)
                #发消息
                if data == 'ba_poses':
                    response = get_ba_poses()
                elif data == 'com3d':
                    response = get_com3d()
                elif data == 'com2d':
                    response = get_com2d()
                elif data == 'com2d_ba':
                    response = get_com2d_ba()
                elif data == 'hello':
                    response = greeting()
                else:
                    response = '404 Not Found\n'
                if response[-1]!='\n': 
                    response = response + '\n'
                self.request.sendall(response.encode('utf-8'))
        except ConnectionResetError:
            print('ConnectionResetError')
        except Exception as e:
            print(e)
        print('Closed a request')


if __name__ == "__main__":
    # Create the server, binding to localhost on port 9999
    with ThreadedTCPServer((HOST, PORT), MyTCPHandler) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        print('Running realtime position daemon.')
        server.serve_forever()