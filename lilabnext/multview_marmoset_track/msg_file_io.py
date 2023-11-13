import fcntl
import os.path as osp
import datetime
import time
import json
import argparse


files = {'com2d': '/mnt/tmp/com2d_msg.lock',
         'com2d_ba': '/mnt/tmp/com2d_ba_msg.lock',
         'com3d': '/mnt/tmp/com3d_msg.lock'}

file_handles = {k: open(files[k], 'r+') for k in files}

def acquire_lock(file_handle, max_attempts=200, retry_interval=0.05):
    attempts = 0
    while attempts < max_attempts:
        try:
            fcntl.flock(file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True  # 成功获取锁
        except BlockingIOError:
            attempts += 1
            time.sleep(retry_interval)
    
    return False  # 获取锁失败

def write_msg(msg, file_key='com3d', with_date=True):
    file_handle = file_handles[file_key]
    if acquire_lock(file_handle):
        if with_date:
            t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            msg = f'{t}\t{msg}'
        file_handle.seek(0)
        file_handle.truncate()
        file_handle.write(f'{msg}\n')
        file_handle.flush()
        fcntl.flock(file_handle, fcntl.LOCK_UN)
    else:
        raise Exception('获取锁失败')

def read_msg(file_key='com3d'):
    msg=''
    file_handle = file_handles[file_key]
    file_handle.seek(0)
    if acquire_lock(file_handle):
        msg = file_handle.read()
        fcntl.flock(file_handle, fcntl.LOCK_UN)
    else:
        raise Exception('获取锁失败')
    return msg

def read_com2d():
    return read_msg('com2d')

def read_com3d():
    return read_msg('com3d')

def read_com2d_ba():
    return read_msg('com2d_ba')

def write_calibpkl_msg(ba_poses:dict):
    file_path = osp.join('/mnt/tmp', f'ba_poses.lock')
    file_handle = open(file_path, 'w')
    file_handle.write(json.dumps(ba_poses))
    file_handle.close()

def read_calibpkl_msg():
    file_path = osp.join('/mnt/tmp', f'ba_poses.lock')
    file_handle = open(file_path, 'r')
    ba_poses = file_handle.read()
    file_handle.close()
    return ba_poses