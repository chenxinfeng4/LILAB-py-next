#
import os.path as osp
from lilab.cvutils_new.dehead_video import dehead

vfile = '/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-1-31_sync/ledon/2024-01-31_13-42-57.mp4'
# dehead_in_high = [1,0,0,2,2,4]
dehead_in_high = [2,0,0,2,0,3]

def dehead_video_mkv(vfile, dehead_in_high):
    ncam = len(dehead_in_high)
    ext = osp.splitext(vfile)[1]
    if ext == '.mp4':
        vfile_prefix = osp.splitext(vfile)[0]
        print('自动查找mkv')
    elif ext == '.mkv':
        assert '_cam' in vfile
        vfile_prefix = vfile.split('_cam')[0]
    else:
        raise NotImplementedError(ext)

    vfilemkv_l = [vfile_prefix + f'_cam{i+1}.mkv' for i in range(ncam)]
    assert all(osp.isfile(f) for f in vfilemkv_l)

    for dehead_num, vfilemkv in zip(dehead_in_high, vfilemkv_l):
        dehead(vfilemkv, dehead_num)
    print('Done all dehead')

dehead_video_mkv(vfile, dehead_in_high)