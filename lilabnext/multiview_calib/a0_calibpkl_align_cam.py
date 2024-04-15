#%%
# python -m lilabnext.multview_marmoset_track.a0_calibpkl_align_cam xxx*.calibpkl --rescale 0.001
import pickle
import numpy as np
import argparse
import copy
import os.path as osp


def get_cam_pos(R,t):
    cam_pos = (- np.linalg.inv(R) @ t.reshape(-1, 1)).ravel()
    return cam_pos

def move_axis_oringe(ba_poses, dxyz):
    ba_poses = copy.deepcopy(ba_poses)
    dxyz = np.array(dxyz).reshape(-1, 1)
    for i in range(len(ba_poses)):
        ba_poses[i]['t'] += (ba_poses[i]['R']@dxyz).ravel()
    return ba_poses


def rotate_axis_oringe(ba_poses, r_inv):
    ba_poses = copy.deepcopy(ba_poses)
    for i in range(len(ba_poses)):
        ba_poses[i]['R'] = ba_poses[i]['R']@r_inv
    return ba_poses

def scale_axis_oringe(ba_poses, scale):
    ba_poses = copy.deepcopy(ba_poses)
    for i in range(len(ba_poses)):
        ba_poses[i]['t'] = ba_poses[i]['t']*scale
    return ba_poses

def convert(calibpkl:str, iviewalign:int=-1, rescale:float=1.0):
    pkldata=pickle.load(open(calibpkl,'rb'))
    ba_poses = pkldata['ba_poses']
    nview = max(ba_poses.keys()) + 1
    iviewalign = np.arange(nview)[iviewalign]

    for k in ba_poses:
        for vk in ['R', 't']:
            ba_poses[k][vk] = np.array(ba_poses[k][vk], dtype=float)

    R_i, t_i = ba_poses[iviewalign]['R'], ba_poses[iviewalign]['t']
    cam_pos_i = get_cam_pos(R_i, t_i)
    R_inv_i = np.linalg.inv(R_i)
    ba_poses2 = move_axis_oringe(ba_poses, cam_pos_i)
    ba_poses3 = rotate_axis_oringe(ba_poses2, R_inv_i)
    ba_poses4 = scale_axis_oringe(ba_poses3, rescale)
    pkldata['ba_poses'] = ba_poses4
    output_pkl = osp.splitext(calibpkl)[0] + '.aligncalibpkl'
    pickle.dump(pkldata, open(output_pkl, 'wb'))
    return output_pkl


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('calibpkl', type=str, help='calib pkl')
    parser.add_argument('--iview-align', type=int, default=-1, help='iview align')
    parser.add_argument('--rescale', type=float, default=1, help='rescale')
    args = parser.parse_args()
    convert(args.calibpkl, args.iview_align, args.rescale)
