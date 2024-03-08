#%%
import yaml
import numpy as np
import argparse

yaml_file='/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-1-31_sync/ballmove/2024-01-31_13-47-48.timeOrder'


def assert_trans_order(order:list):
    camid_set = []
    for camid in order:
        if camid is None or camid == 'x':
            continue
        else:
            assert isinstance(camid,int) and camid>=1, 'camid must be int and >=1'
        camid_l = []
        while True:
            camid_l.append(camid % 10)
            camid = camid // 10
            if camid == 0:
                break
        camid_set.extend(camid_l)

    camids, camidc = np.unique(camid_set, return_counts=True)
    assert camidc.max() == 1, 'camid must be unique'
    assert camids.min() in [0, 1], 'camid must start from 0/1'
    assert np.ptp(camids) == len(camids)-1, 'camid must be consecutive'
    ncam = len(camid_set)
    isstart1 = camids.min() == 1
    return ncam, isstart1


def get_head_num(order:list, ncam:int, isstart1:bool) -> np.ndarray:
    heads = np.zeros(ncam, dtype=int) - 100
    for headc, camid in enumerate(order):
        if camid is None or camid is 'x':
            continue
        else:
            assert isinstance(camid,int) and camid>=1, 'camid must be int and >=1'
        while True:
            camid_ = (camid % 10)
            heads[camid_ - isstart1] = headc
            camid = camid // 10
            if camid == 0:
                break
    assert np.all(heads >= 0)
    return heads


def main(yaml_file:str):
    with open(yaml_file, 'r') as f:
        result = yaml.safe_load(f)

    trans_order_low  = result['low']
    trans_order_high = result['high']
    ncam, isstart1 = assert_trans_order(trans_order_low)
    ncam_, isstart1_ = assert_trans_order(trans_order_high)
    assert (ncam, isstart1) == (ncam_, isstart1_), 'trans_order_low and trans_order_high must have the same number of cameras'

    heads_low = get_head_num(trans_order_low, ncam, isstart1)
    heads_high = get_head_num(trans_order_high, ncam, isstart1)
    dehead_in_low = result.get('dehead_in_low', [0]*len(heads_low))
    heads_low_ = heads_low - dehead_in_low
    dehead_in_high:np.ndarray = heads_high - heads_low_
    dehead_in_high -= dehead_in_high.min()

    result['dehead_in_high'] = dehead_in_high.tolist()
    result['dehead_in_low'] = dehead_in_low

    with open(yaml_file, 'w') as f:
        yaml.dump(result, f)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('yaml_file', type=str, help='path to yaml file')
    args = parser.parse_args()
    main(args.yaml_file)
