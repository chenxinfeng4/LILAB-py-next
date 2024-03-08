# python -m lilab.multiview_scripts_dev.s2_matpkl2ballpkl ../data/matpkl/ball.matpkl --time 1 12 24 35 48
import argparse
from .video_set_reader import VideoSetReader

from ffmpegcv.ffmpeg_reader_pannels import FFmpegReaderPannels
from lilab.multiview_scripts_dev.s2_matpkl2ballpkl import convert
import lilab.multiview_scripts_dev.s2_matpkl2ballpkl as s2


def get_background_img(global_iframe, vfile, views_xywh):
    if '_cam' in vfile:
        vin = VideoSetReader(vfile, nvideo=len(views_xywh))
    else:
        vin = FFmpegReaderPannels.VideoReader(vfile, views_xywh)
    ret, background_img = vin.read()
    vin.release()

    assert ret, "Failed to read frame {}".format(0)
    return background_img

s2.get_background_img = get_background_img
s2.nchoose = 2000

# %%
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('matfile', type=str)
    parser.add_argument('--time', type=float, nargs='+')
    parser.add_argument('--force-setupname', type=str, default=None)
    args = parser.parse_args()
    assert len(args.time) == 5, "global_time should be 5 elements"
    convert(args.matfile, args.time, args.force_setupname)
