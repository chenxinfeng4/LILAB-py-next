#%%
import numpy as np
import ffmpegcv
import os.path as osp
import os
from ffmpegcv.ffmpeg_reader import FFmpegReader


def find_sibling_video(video_first_file, nvideo):
    basename = osp.basename(video_first_file)
    if '0' in basename and '1' in basename:
        start_from = 0 if basename.rfind('0') > basename.rfind('1') else 1
    elif '0' in basename and not '1' in basename:
        start_from = 0
    elif not '0' in basename and '1' in basename:
        start_from = 1
    else:
        raise ValueError('video_first_file should contain 0 or 1')
    
    last_index = video_first_file.rfind(str(start_from))
    video_files = [video_first_file[:last_index]+str(i)+video_first_file[last_index+1:]
                    for i in range(start_from,nvideo+start_from)]
    assert all(osp.exists(f) for f in video_files), 'video_first_file not exists'
    return video_files


class VideoSetReader:
    def __init__(self, video_first_file:str, nvideo:int,*args, **kwargs):
        assert nvideo>=2, 'nvideo should be >=2'
        video_files = find_sibling_video(video_first_file, nvideo)
        print('video_files found OK:')

        self.vid_list = [ffmpegcv.VideoCapture(f, *args, **kwargs) for f in video_files]
        self.iframe = -1
        self._isopen = True
        self.count = min([len(vid) for vid in self.vid_list])
        self.fps = self.vid_list[0].fps
        self.pix_fmt = self.vid_list[0].pix_fmt
        assert set([vid.fps for vid in self.vid_list])=={self.fps}, 'fps not same'
        out_numpy_shapes = [vid.out_numpy_shape for vid in self.vid_list]
        if set(out_numpy_shapes):
            self.out_numpy_shape = (nvideo, *out_numpy_shapes[0])
        else:
            self.out_numpy_shape = None

    def release(self):
        self._isopen = False
        for vid in self.vid_list:
            vid.release()

    def __exit__(self, type, value, traceback):
        self.release()

    def __len__(self):
        return self.count

    def read(self):
        rets, views = zip(*[vid.read() for vid in self.vid_list])
        ret = all(rets)
        if ret:
            self.iframe += 1
            if self.out_numpy_shape:
                views = np.stack(views, axis=0)
            return ret, views
        else:
            return ret, None

class StreamRTSetReader:
    def __init__(self, video_files:list, camsize_wh:list,*args, **kwargs):
        nvideo = len(video_files)
        assert nvideo>=2, 'nvideo should be >=2'
        print('video_files found OK:')

        self.vid_list = [ffmpegcv.VideoReaderStreamRT(f, *args, camsize_wh=camsize_wh,**kwargs)
                            for f in video_files]
        self.iframe = -1
        self._isopen = True
        self.count = None
        self.pix_fmt = self.vid_list[0].pix_fmt
        out_numpy_shapes = [vid.out_numpy_shape for vid in self.vid_list]
        if set(out_numpy_shapes):
            self.out_numpy_shape = (nvideo, *out_numpy_shapes[0])
        else:
            self.out_numpy_shape = None

    def release(self):
        self._isopen = False
        for vid in self.vid_list:
            vid.release()

    def __exit__(self, type, value, traceback):
        self.release()
    
    def __iter__(self):
        return self

    def __len__(self):
        return None
    
    def __next__(self):
        ret, img = self.read()
        if ret:
            return img
        else:
            raise StopIteration

    def read(self):
        rets, views = zip(*[vid.read() for vid in self.vid_list])
        ret = all(rets)
        if ret:
            self.iframe += 1
            if self.out_numpy_shape:
                views = np.stack(views, axis=0)
            return ret, views
        else:
            return ret, None
        

class VideoSetCanvasReader(FFmpegReader):
    def __init__(self, video_first_file:str, nvideo = 6, resize: tuple=None, pix_fmt='bgr24'):
        super().__init__()
        
        video_files = find_sibling_video(video_first_file, nvideo)
        self.vid_list = [ffmpegcv.VideoCapture(f) for f in video_files]
        self.fps = self.vid_list[0].fps
        self.pannel_width = self.vid_list[0].width
        self.pannel_height = self.vid_list[0].height
        self.origin_width = self.pannel_width * 3
        self.origin_height = self.pannel_height * 1
        self.count = min([len(vid) for vid in self.vid_list])
        assert set([vid.fps for vid in self.vid_list])=={self.fps}, 'fps not same'
        self.width, self.height = resize if resize else (self.origin_width, self.origin_height)
        for vid in self.vid_list:
            vid.release()
        resize_opt = f'[origin],[origin]scale={resize[0]}:{resize[1]}' if resize else ''
        self.ffmpeg_cmd = (
            f'ffmpeg -loglevel warning '
            f' -i {video_files[0]} -i {video_files[1]} -i {video_files[2]} '
            f' -filter_complex "'
            '[0:v][1:v][2:v]xstack=inputs=3:layout=0_0|w0_0|w0+w0_0'
            f'{resize_opt}" '
            f' -pix_fmt {pix_fmt} -r {self.fps} -f rawvideo pipe:'
        )
        self.out_numpy_shape = {
            "rgb24": (self.height, self.width, 3),
            "bgr24": (self.height, self.width, 3),
            "nv12": (int(self.height * 1.5), self.width),
            "yuv420p": (int(self.height * 1.5), self.width),
            "gray": (self.height, self.width, 1)
        }[pix_fmt]



def extract(video_first_file, numframe_to_extract, maxlength= 9000):
    import tqdm
    import cv2

    video_input = video_first_file
    frame_dir = "outframes"
    frame_min_interval = 100

    dirname,filename=osp.split(video_input)
    nakefilename = osp.splitext(filename)[0]
    cap = VideoSetCanvasReader(video_input)
    os.makedirs(osp.join(dirname, frame_dir), exist_ok = True)
    length = cap.count
    length = min([maxlength, length-1]) if maxlength else length-1
    downsample_length = length // frame_min_interval
    np.random.seed(0)
    idxframe_to_extract = set(np.random.permutation(downsample_length)[:numframe_to_extract]*frame_min_interval + 5)
    idxframe_max = max(idxframe_to_extract)

    for iframe in tqdm.tqdm(range(length)):
        ret, frame = cap.read()
        if not ret: break
        if iframe>idxframe_max: break
        if iframe not in idxframe_to_extract: continue
        filename = osp.join(dirname, frame_dir, nakefilename + '_{0:06}.jpg'.format(iframe))
        cv2.imwrite(filename, frame, [int(cv2.IMWRITE_JPEG_QUALITY),100])
        
    cap.release()


if __name__ == '__main__':
    video_first_file = '/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera6/20230824/ball_vid1_c.mp4'
    vid = VideoSetCanvasReader(video_first_file, resize=(1280, 800))
    for i, frame in enumerate(vid):
        print(i)
        print(frame.shape)
        if i>100:
            break

    video_first_file = '/mnt/liying.cibr.ac.cn_Data_Temp/marmoset_camera6/20230824/one_monkey_vid1.mp4'
    extract(video_first_file, 20, maxlength= 9000)