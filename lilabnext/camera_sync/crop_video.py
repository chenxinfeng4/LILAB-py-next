from lilab.cameras_setup import get_view_xywh_wrapper
import lilab.cvutils.crop_videofast as c

c.nviews = 'frank'
crop_xywh = get_view_xywh_wrapper('frank')

vfile='/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera3_cxf/2024-1-31_sync/ballmove/2024-01-31_13-47-48ballmove.mp4'
c.main(vfile)
