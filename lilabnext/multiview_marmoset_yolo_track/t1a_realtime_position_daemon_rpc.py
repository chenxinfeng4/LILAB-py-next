#%%
import picklerpc
import numpy as np
from multiview_calib.calibpkl_predict import CalibPredict

HOST, PORT = "0.0.0.0", 8090


files = {'com2d': [''],
        'com2d_ba': [''],
        'com3d': [''],
        'p3d': [''],
        'p2d': [''],
        'ba_poses':'',
        'ba_poses_full':'',
        'calibobj':'',
        'calibobj_full':'',
        'nclass':None,
        'nins':None,
        'p3d_last': [],
        'ptz_ip_port_list':[],
        'ptz_baseline_list':[]}


def greeting():
    return "Welcome to the marmoset tracker!\n"

def com2d(*value):
    if len(value)==0:
        return files['com2d']
    else:
        files['com2d'] = value

def com2d_ba(*value):
    if len(value)==0:
        return files['com2d_ba']
    else:
        files['com2d_ba'] = value

def com3d(*value):
    if len(value)==0:
        return files['com3d']
    else:
        files['com3d'] = value

def p3d(*value):
    if len(value)==0:
        return files['p3d']
    else:
        files['p3d'] = value

def p3d_last(value=None):
    if value is None:
        return files['p3d_last']
    else:
        files['p3d_last'] = value

def p2d(*value):
    if len(value)==0:
        return files['p2d']
    else:
        files['p2d'] = value
    
def ba_poses(value=None):
    if value is None:
        return files['ba_poses']
    else:
        files['calibobj'] = CalibPredict({'ba_poses':value})
        files['ba_poses'] = value

def ba_poses_full(value=None):
    if value is None:
        return files['ba_poses_full']
    else:
        files['calibobj_full'] = CalibPredict({'ba_poses':value})
        files['ba_poses_full'] = value

def nclass(value=None):
    if value is None:
        return files['nclass']
    else:
        files['nclass'] = value

def nins(value=None):
    if value is None:
        return files['nins']
    else:
        files['nins'] = value

def ptz_ip_port_list(value=None):
    if value is None:
        return files['ptz_ip_port_list']
    else:
        files['ptz_ip_port_list'] = value
    
def ptz_baseline_list(value=None):
    if value is None:
        return files['ptz_baseline_list']
    else:
        files['ptz_baseline_list'] = value


def process_p2d(p2d:np.ndarray, ijoint:int, iframe:int) -> None:
    calibobj = files['calibobj']
    if not hasattr(calibobj, 'last_keypoints_xyz_ba'):
        calibobj.last_keypoints_xyz_ba = p2d*0.0
    keypoints_xyz_ba = calibobj.p2d_to_p3d(p2d)  #nanimal, 3
    isnan = np.isnan(keypoints_xyz_ba)
    if np.any(isnan):
        keypoints_xyz_ba[isnan] = calibobj.last_keypoints_xyz_ba[isnan]
    calibobj.last_keypoints_xyz_ba = keypoints_xyz_ba
    keypoints_xy_ba = calibobj.p3d_to_p2d(keypoints_xyz_ba)
    p3d(iframe, keypoints_xyz_ba)

    if ijoint is not None:
        keypoints_xyz_ba = keypoints_xyz_ba[ijoint].ravel()
        keypoints_xy_ba = keypoints_xy_ba[:,ijoint]
    com2d_ba(iframe, keypoints_xy_ba)
    com3d(iframe, keypoints_xyz_ba)

def process_p2d_multiins(p2d:np.ndarray, iclass:int, iframe:int) -> None:
    calibobj = files['calibobj']
    if not hasattr(calibobj, 'last_keypoints_xyz_ba'):
        calibobj.last_keypoints_xyz_ba = p2d*0.0
    nview, nclass, nins, ndim = p2d.shape


def p3d_alignbycam(p3d:np.ndarray, icam:int) -> np.ndarray:
    calibobj = files['calibobj_full']
    if not hasattr(calibobj, 'last_keypoints_xyz_ba'):
        calibobj.last_keypoints_xyz_ba = p3d * 0.0

    p3d_align = calibobj.p3d_alignby_cam(icam, p3d)
    return p3d_align


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
    server.register_function(p3d)
    server.register_function(p2d)
    server.register_function(ba_poses)
    server.register_function(ba_poses_full)
    server.register_function(nclass)
    server.register_function(nins)
    server.register_function(ptz_ip_port_list)
    server.register_function(ptz_baseline_list)
    server.register_function(process_p2d)
    server.register_function(p3d_alignbycam)
    server.register_function(p3d_last)
    server.serve_forever()

    