#
import numpy as np
trans_order_low = [5,6,[1,2,3,4]]    #相机时间戳跳变的先后顺序
trans_order_high = [5,[2,3],1,[4,6]] #相机时间戳跳变的先后顺序
dehead_in_low = [0,0,0,0,1,1]        #低清相机灯光滞后检测

def assert_trans_order(order):
    camid_set = []
    for camid in order:
        if camid is None or camid == []:
            continue
        if not isinstance(camid,list):
            camid = [camid]
        camid_set.extend(camid)
    camids, camidc = np.unique(camid_set, return_counts=True)
    assert camidc.max() == 1, 'camid must be unique'
    assert camids.min() in [0, 1], 'camid must start from 0/1'
    assert np.ptp(camids) == len(camids)-1, 'camid must be consecutive'
    ncam = len(camid_set)
    isstart1 = camids.min() == 1
    return ncam, isstart1


def get_head_num(order, ncam, isstart1):
    heads = np.zeros(ncam, dtype=int) - 100
    for headc, camid in enumerate(order):
        if camid is None or camid == []:
            continue
        if not isinstance(camid,list):
            camid = [camid]
        for camid_ in camid:
            heads[camid_ - isstart1] = headc
    return heads


def main(trans_order_low, trans_order_high, dehead_in_low):
    ncam, isstart1 = assert_trans_order(trans_order_low)
    ncam_, isstart1_ = assert_trans_order(trans_order_high)
    assert (ncam, isstart1) == (ncam_, isstart1_), 'trans_order_low and trans_order_high must have the same number of cameras'

    heads_low = get_head_num(trans_order_low, ncam, isstart1)
    heads_high = get_head_num(trans_order_high, ncam, isstart1)
    assert np.all(heads_low>=0) and np.all(heads_high>=0)

    heads_low_ = heads_low - dehead_in_low

    dehead_in_high = heads_high - heads_low_
    dehead_in_high -= dehead_in_high.min()
    print('Dehead num is {}'.format(','.join(map(str, dehead_in_high))))


if __name__ == '__main__':
    main(trans_order_low, trans_order_high, dehead_in_low)