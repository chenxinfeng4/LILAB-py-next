from lilabnext.multiview_marmoset_yolo_track.t2_point3d_set_ptzf import PtzControl, log_deamond_start
import argparse
import os.path as osp
import numpy as np
import lilabnext.multiview_marmoset_yolo_track.t1a_realtime_position_daemon_rpc as sockserver
from lilabnext.multiview_calib.focus_length import zf_interp_industry
import time


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server-ip-port', type=str, default='localhost:8090')
    parser.add_argument('--zfmappkl', type=str)
    parser.add_argument('--ptz-ip-port-list', nargs='*', type=str)
    parser.add_argument('--baseline-ptz-list', nargs='*', type=str)
    parser.add_argument('--iclass-list', nargs='*', type=int)
    args = parser.parse_args()
    serve_ip, serve_port = args.server_ip_port.split(':')
    ptz_ip_port_l = np.array([s.split(':') 
                              for s in args.ptz_ip_port_list])
    baseline_ptz_l = np.array([[float(n) for n in ptz.split(',')] 
                               for ptz in args.baseline_ptz_list])
    iins_l = args.iclass_list

    assert osp.exists(args.zfmappkl), 'zfmappkl not exists'
    zf_interp_fun = zf_interp_industry(args.zfmappkl)

    rpc_client = sockserver.create_client()
    rpc_client.ptz_ip_port_list(ptz_ip_port_l)
    rpc_client.ptz_baseline_list(baseline_ptz_l)
    log_deamond_start()
    ptzControler_l = [PtzControl(ip=ptz_ip, port=ptz_port, 
                              baseline_ptz=baseline_ptz, zf_interp_fun=zf_interp_fun)
                        for (ptz_ip, ptz_port), baseline_ptz in zip(ptz_ip_port_l, baseline_ptz_l)]

    ncam_localize = len(rpc_client.ba_poses())
    ncam_ptzf = len(rpc_client.ba_poses_full()) - ncam_localize
    icam_ptzf = np.arange(ncam_ptzf) + ncam_localize
    assert len(ptz_ip_port_l)==len(baseline_ptz_l)==len(iins_l)==ncam_ptzf
    
    while True:
        iframe, object_p = rpc_client.com3d()
        rpc_client.p3d_last(object_p)
        for icam, iins, ptzControler in zip(icam_ptzf, iins_l, ptzControler_l):
            p3d_align = rpc_client.p3d_alignbycam(object_p[iins], icam)
            camera_s = ptzControler(p3d_align)
        time.sleep(0.02)
