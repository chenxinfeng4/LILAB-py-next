import datetime
import json

files = {'com2d': '',
        'com2d_ba': '',
        'com3d': '',
        'ba_poses':''}

def write_msg(msg, file_key='com3d', with_date=True):
    if with_date:
        t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        msg = f'{t}\t{msg}'
    files[file_key] = msg

def read_msg(file_key='com3d'):
    msg=files[file_key] 
    return msg

def read_com2d():
    return read_msg('com2d')

def read_com3d():
    return read_msg('com3d')

def read_com2d_ba():
    return read_msg('com2d_ba')

def write_calibpkl_msg(ba_poses:dict):
    for k in ba_poses:
        for kk in ba_poses[k]:
            if isinstance(ba_poses[k][kk], list): continue
            ba_poses[k][kk] = ba_poses[k][kk].tolist()
    write_msg(json.dumps(ba_poses), file_key='ba_poses', with_date=False)

def read_calibpkl_msg():
    return read_msg('ba_poses')
