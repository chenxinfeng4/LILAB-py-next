# %%
import scipy.io as sio
import numpy as np

matfile = '/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera6/20230817/intrinsic_cv.mat'
matdata  = sio.loadmat(matfile)
# %%
assert {'IntrinsicMatrix_cv_list', 'distort_cv_list'} <= set(matdata.keys())
ncam, i1, i2 = matdata['IntrinsicMatrix_cv_list'].shape
assert matdata['distort_cv_list'].shape[0] == ncam
assert i1==i2==3

# %%
for i in range(ncam):
    print(f'=========={i}==========')
    print(np.array2string(matdata['IntrinsicMatrix_cv_list'][i], separator=","))
    print(np.array2string(matdata['distort_cv_list'][i], separator=","))

