# from lilabnext.camera_sync.mkv_videos_reader import get_mkv_reader
#%%
import yaml
import os.path as osp
import ffmpegcv
from ffmpegcv.ffmpeg_reader import FFmpegReader
import numpy as np


class VideoSetReader(FFmpegReader):
    def __init__(self, video_mp4_file:str, num_dehead:list=None, nvideo:int=None, *args, **kwargs):
        assert osp.exists(video_mp4_file), f'{video_mp4_file} does not exist.'
        assert num_dehead is not None or nvideo is not None, 'At least one of num_dehead and nvideo should be provided.'
        if nvideo is not None:
            if num_dehead is None:
                num_dehead = [0] * nvideo
            assert len(num_dehead) == nvideo, 'num_dehead should have the same length as nvideo.'
        else:
            nvideo = len(num_dehead)
        
        video_files = [osp.splitext(video_mp4_file)[0] + f'_cam{i+1}.mkv' for i in range(nvideo)]
        self.vid_list = [ffmpegcv.VideoCaptureNV(f, *args, gpu=igpu, **kwargs) for igpu,f in enumerate(video_files)]
        
        # dehead first frames to get aligned timestamp
        for n, vid in zip(num_dehead, self.vid_list):
            for _ in range(n): vid.read()

        counts = np.array([len(vid) for vid in self.vid_list])
        counts_dehead = counts - num_dehead
        self.count = counts_dehead.min()
        self.fps = self.vid_list[0].fps
        self.pix_fmt = self.vid_list[0].pix_fmt
        self.iframe = -1
        self._isopen = True
        out_numpy_shapes = [vid.out_numpy_shape for vid in self.vid_list]
        self.out_numpy_shape = (nvideo, *out_numpy_shapes[0])

    def release(self):
        self._isopen = False
        for vid in self.vid_list:
            vid.release()

    def read(self):
        rets, views = zip(*[vid.read() for vid in self.vid_list])
        ret = all(rets)
        if ret:
            self.iframe += 1
            # if self.out_numpy_shape:
            #     views = np.stack(views, axis=0)
            return ret, views
        else:
            return ret, None


def get_mkv_reader(video_mp4_file, *args, **kwargs) -> VideoSetReader:
    timeOrder_file = video_mp4_file.replace('.mp4', '.timeOrder')
    assert osp.isfile(timeOrder_file)
    with open(timeOrder_file, 'r') as f:
        result = yaml.safe_load(f)
    num_dehead = result['dehead_in_high']
    return VideoSetReader(video_mp4_file, num_dehead, *args, **kwargs)