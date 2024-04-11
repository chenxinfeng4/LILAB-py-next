#%%
import picklerpc
import numpy as np

HOST, PORT = "0.0.0.0", 8090


files = {'com2d': '',
        'com2d_ba': '',
        'com3d': '',
        'ba_poses':''}


def greeting():
    return "Welcome to the marmoset tracker!\n"

def com3d(value=None):
    if value is None:
        return files['com3d']
    else:
        files['com3d'] = value

def com2d(value=None):
    if value is None:
        return files['com2d']
    else:
        files['com2d'] = value

def com2d_ba(value=None):
    if value is None:
        return files['com2d_ba']
    else:
        files['com2d_ba'] = value
        
def ba_poses(value=None):
    if value is None:
        return files['ba_poses']
    else:
        files['ba_poses'] = value


server = picklerpc.PickleRPCServer((HOST, PORT))

def get_number_of_connections():
    return server.n_connection

def create_client(host='localhost', port=PORT) -> picklerpc.PickleRPCClient:
    return picklerpc.PickleRPCClient((host, port))

def serve_forever():
    server.register_function(greeting)
    server.register_function(com3d)
    server.register_function(com2d)
    server.register_function(com2d_ba)
    server.register_function(ba_poses)
    server.serve_forever()

    