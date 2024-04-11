#%%
import pickle
import os.path as osp
import scipy.io as sio
import numpy as np
import matplotlib.pyplot as plt
import argparse


kpt_file = '/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-4-10_Camera_calibration/Low/focal_length/anno.mat'
PTZF_page = """
Pan: 274.85
Tilt: 63.08
Zoom: 3.0
Focus: 40544

Pan: 275.03
Tilt: 61.12
Zoom: 3.7
Focus: 43116

Pan: 273.82
Tilt: 59.49
Zoom: 4.5
Focus: 44920

Pan: 274.02
Tilt: 58.12
Zoom: 4.7
Focus: 45607

Pan: 272.81
Tilt: 56.98
Zoom: 5.4
Focus: 47188

Pan: 271.76
Tilt: 55.36
Zoom: 6.4
Focus: 48500

Pan: 304.86
Tilt: 50.25
Zoom: 6.7
Focus: 48866

Pan: 247.72
Tilt: 32.1
Zoom: 7.5
Focus: 48929
"""

    
def zf_interp_industry(zfmappkl) -> callable:
    data = pickle.load(open(zfmappkl, 'rb'))
    dist, zf = data['dist'], data['zf']
    dist_min, dist_max = dist.min(), dist.max()
    def f(dist_now) -> np.ndarray:
        np.clip(dist_now, dist_min, dist_max)
        return np.stack([np.interp(dist_now, dist, zf[:,0]),
                        np.interp(dist_now, dist, zf[:,1])], axis=-1)
    return f


def main(kpt_file, PTZF_page):
    kpt_data = sio.loadmat(kpt_file)

    p3d = kpt_data['data_3D'][:,:3]
    p_l, t_l, z_l, f_l = [], [], [], []
    for line in PTZF_page.split('\n'):
        if 'Pan' in line:
            p_l.append(float(line.split(':')[1]))
        if 'Tilt' in line:
            t_l.append(float(line.split(':')[1]))
        if 'Zoom' in line:
            z_l.append(float(line.split(':')[1]))
        if 'Focus' in line:
            f_l.append(float(line.split(':')[1]))

    ptzf_l = np.array([p_l, t_l, z_l, f_l]).T
    dist = np.linalg.norm(p3d, axis=-1)
    zf = ptzf_l[:,2:]

    # plot figure
    fig, ax = plt.subplots(2,2, figsize=(6,6))
    plt.sca(ax[0,0])
    plt.plot(dist, zf[:,0], 'o')
    plt.xlabel('distance (m)')
    plt.ylabel('zoom factor')

    plt.sca(ax[0,1])
    plt.plot(dist, zf[:,1], 'o')
    plt.xlabel('distance (m)')
    plt.ylabel('focus factor')

    plt.sca(ax[1,0])
    plt.plot(zf[:,0], zf[:,1], 'o')
    plt.xlabel('zoom factor')
    plt.ylabel('focus factor')

    plt.tight_layout()

    plt.sca(ax[1,1])
    plt.axis('off')

    outfig = osp.join(osp.dirname(kpt_file), 'focus_length_zfmap.jpg')
    plt.savefig(outfig)

    # savefile
    outdata = {
        'dist': dist,
        'zf': zf
    }
    outpkl = osp.join(osp.dirname(kpt_file), 'focus_length.zfmappkl')
    pickle.dump(outdata, open(outpkl, 'wb'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--kpt_file', type=str, default=kpt_file)
    parser.add_argument('--PTZF_page', type=str, default=PTZF_page)
    args = parser.parse_args()

    main(args.kpt_file, args.PTZF_page)
