# from lilabnext.multview_marmoset_track.a0b_calibpkl_rescale_mkv 
#%%
import pickle
import numpy as np
import argparse
import copy
import os.path as osp

calibpkl = '/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-1-31_sync/ballmove/ball_move_cam1.calibpkl'
resize_wh = [2560, 1440]

#%%
def convert(calibpkl:str, resize_wh:list):
    resize_wh = np.array(resize_wh)

    pkldata=pickle.load(open(calibpkl,'rb'))
    ba_poses = copy.deepcopy(pkldata['ba_poses'])
    nview = len(ba_poses)
    image_wh_shapes = np.array([ba_poses[i]['image_shape'] for i in range(nview)])[...,::-1]
    image_wh_scale = resize_wh / image_wh_shapes
    for i in range(nview):
        ba_poses[i]['image_shape'] = resize_wh[::-1].tolist()
        scale_np = np.array([*image_wh_scale[i], 1])[:,None]
        ba_poses[i]['K'] = np.round(np.array(ba_poses[i]['K']) * scale_np, 1)

    outdict = {'ba_poses': ba_poses,
               'setup': pkldata['setup'],
               'intrinsics': ba_poses}
    
    output_pkl = osp.splitext(calibpkl)[0] + '.mkv.calibpkl'
    pickle.dump(outdict, open(output_pkl, 'wb'))
    return output_pkl


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('calibpkl', type=str, help='calib pkl')
    parser.add_argument('--resize_wh', nargs='+', type=float, default=resize_wh, help='rescale')
    args = parser.parse_args()
    convert(args.calibpkl, args.resize_wh)
