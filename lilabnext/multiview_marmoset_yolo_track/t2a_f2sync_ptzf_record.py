#%%
import lilabnext.multiview_marmoset_yolo_track.t1a_realtime_position_daemon_rpc as sockserver
import numpy as np
from lilabnext.multview_marmoset_track.a1_ptz_control import status_PTZF
import tqdm
import time
from itertools import count
from scipy import interpolate
import picklerpc
import datetime
from multiview_calib.calibpkl_predict import CalibPredict
import pickle
import threading


# ====== f2 同步助手 ========
HOST, PORT = "0.0.0.0", 8091
outdir = '/mnt/e/marmoset_view6/'
rpc_f2sync_server = picklerpc.PickleRPCServer((HOST, PORT))

__status = False #not start
__thread = None

def status() -> bool:
    return __status

def switch(status:bool):
    global __status, __thread
    if __status==status: return
    __status = status
    
    # create a thread running `one_record_task`
    if status==True:
        __thread = threading.Thread(target=one_record_task)
        __thread.start()
    

rpc_f2sync_server.register_function(status)
rpc_f2sync_server.register_function(switch)


def create_client(host='localhost', port=PORT) -> picklerpc.PickleRPCClient:
    return picklerpc.PickleRPCClient((host, port))


def get_ptzf():
    rpc_client = sockserver.create_client()
    ba_poses = rpc_client.ba_poses_full()
    ptz_ip_port_list = rpc_client.ptz_ip_port_list()
    ptz_baseline_list = rpc_client.ptz_baseline_list()
    nptz = len(ptz_ip_port_list)
    return rpc_client, ba_poses, ptz_ip_port_list, ptz_baseline_list, nptz

rpc_client, ba_poses, ptz_ip_port_list, ptz_baseline_list, nptz = get_ptzf()
calibobj = CalibPredict({'ba_poses':ba_poses})

def pull_ptzf_list():
    status_fun_list = np.array([status_PTZF(*ptz_ip_port)
                   for ptz_ip_port in ptz_ip_port_list], dtype=np.float16)
    return status_fun_list

def datastorage_itter(ndim=4) -> callable:
    data_container = np.empty((9600, nptz, ndim), dtype=np.float16)
    nsample = 0
    
    def append(ptzf_list:np.ndarray):
        nonlocal nsample
        nonlocal data_container
        if nsample>=len(data_container):
            data_container = np.concatenate([data_container, 
                                             np.empty((9600, nptz, ndim), dtype=np.float16)])
        data_container[nsample] = ptzf_list
        nsample += 1
        return data_container[:nsample]
    
    return append


def one_record_task():
    print('---Start recording----')
    datastorage_append = datastorage_itter()
    com3d_append = datastorage_itter(ndim=3)
    now = datetime.datetime.now()
    formatted_time = now.strftime('%Y-%m-%d_%H-%M-%S')
    filename = outdir + f'/{formatted_time}.rttrackpkl'
    t_bg = time.time()
    t_int = 1/25  #采样率 5Hz

    for i in tqdm.tqdm(count()):
        # 采样
        if i%5==0:
            status_fun_list = pull_ptzf_list()
            ptzf_records = datastorage_append(status_fun_list)
        
        p3d_last = rpc_client.p3d_last()
        animal_p3d = com3d_append(p3d_last)

        # 控制采样率
        t_bg += t_int
        dt = t_bg - time.time()
        if dt>0:
            time.sleep(dt)
        
        if __status == False:
            break

    # p2d
    animal_p2d = calibobj.p3d_to_p2d(animal_p3d.astype(float))
    animal_p2d[-len(ptz_ip_port_list):] = np.nan
    animal_p2d = animal_p2d.astype(np.float16)

    # upsample ptzf_records from 5Hz to 25Hz
    f = interpolate.interp1d(np.arange(5*len(ptzf_records))[::5], ptzf_records, axis=0)
    ptzf_records_25 = f(np.arange(5*(len(ptzf_records)-1)))

    # save data
    outdict = {'ptz_ip_port_list': ptz_ip_port_list,
            'ptz_baseline_list': ptz_baseline_list,
            'ba_poses': ba_poses,
            'ptzf_records': ptzf_records_25,
            'animal_p3d': animal_p3d,
            'animal_p2d': animal_p2d
            }
    pickle.dump(outdict, open(filename, 'wb'))
    print('---Finish recording----')


def log_deamond_start():
    time.sleep(0.1)
    # creat a thread running `rpc_f2sync_server.serve_forever()`
    threading.Thread(target=rpc_f2sync_server.serve_forever).start()


if __name__ == '__main__':
    rpc_f2sync_server.serve_forever()
