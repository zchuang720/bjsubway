import os
import copy
import time
import gc
import queue
import requests
import threading
import hashlib
import cv2
import base64
import subprocess
import matplotlib
import matplotlib.pyplot as plt
import multiprocessing
import logging
import numpy as np
from collections import deque
from urllib.parse import unquote
from PIL import Image, ImageDraw, ImageFont

import config
import properties
# matplotlib.use('agg')


def download(url, save_folder, info=True):
    """
    Downloads a file from the given URL and saves it to the specified folder.

    Parameters:
        url (str): The URL of the file to be downloaded.
        save_folder (str): The folder where the downloaded file will be saved.
        info (bool, optional): Whether to print information about the download progress. 
            Defaults to True.

    Returns:
        str: The file path of the downloaded file.
    """
    if info: print("Downloading file:", url)
    r = requests.get(url)
    file_name = get_download_file_name(url, r.headers)
    file_path = os.path.join(save_folder, file_name)
    file = open(file_path, "wb")
    file.write(r.content)
    file.close()
    if info: print("Finished download:", str(file_path))
    return file_path


def get_download_file_name(url, headers):
    """
    Get the download file name from the given URL and headers.

    Parameters:
        url (str): The URL of the file to be downloaded.
        headers (dict): The headers of the HTTP response.

    Returns:
        str: The download file name extracted from the URL and headers, or the current timestamp if no file name is found.
    """
    filename = ''
    if 'Content-Disposition' in headers and headers['Content-Disposition']:
        disposition_split = headers['Content-Disposition'].split(';')
        if len(disposition_split) > 1:
            if disposition_split[1].strip().lower().startswith('filename='):
                file_name = disposition_split[1].split('=')
                if len(file_name) > 1:
                    filename = unquote(file_name[1]).replace("\"", "").replace("\'", "")
    if not filename and os.path.basename(url):
        filename = os.path.basename(url).split("?")[0]
    if not filename:
        return time.time()
    return filename


def post(url, data, info=True, logger=None):
        """
        This function is responsible for making a POST request to the specified URL in a new thread.

        Parameters:
            url (str): The URL to which the POST request should be made.
            data (dict): The data to be sent in the POST request.
            info (bool, optional): Whether or not to print the response and its text. Defaults to True.
        """
        # 开新线程进行post
        def post_func(url, data, info=True, logger=None):
            r = requests.post(url, json=data, headers={'content-type':'application/json'})
            if info:
                if logger is not None:
                    if isinstance(logger, str):
                        logger = logging.getLogger(logger)
                    logger.info(f'{r} {r.text}')
                else:
                    print(f'{r} {r.text}')
        post_thread = threading.Thread(target=post_func, args=(url, data, info, logger))
        post_thread.start()


def post_file(url, file_path, data=None, info=True):
    """
    Post a file to a specified URL.

    Parameters:
        url (str): The URL to post the file to.
        file_path (str): The path to the file to be posted.
        data (Optional[Dict[str, Any]]): Additional data to be included in the post request. Default is None.
        info (bool): Flag indicating whether to print additional information about the post request. Default is True.

    Returns:
        None
    """
    # 开新线程进行post
    def post_func(url, data, files, info=True):
        print("Uploading:", str(files["file"]))
        r = requests.post(url, data=data, files=files)
        print("Finished upload")
        if info:
            print(r)
            print(r.text)

    files = {"file": open(file_path, "rb")}

    post_thread = threading.Thread(target=post_func, args=(url, data, files, info))
    post_thread.start()


def generate_md5_checksum(input_string):
    """
    Generates an MD5 checksum string from a given input string.

    Args:
        input_string (str): The input string to generate the MD5 checksum for.

    Returns:
        str: The MD5 checksum string.
    """
    md5_hash = hashlib.md5()
    md5_hash.update(input_string.encode('utf-8'))
    checksum = md5_hash.hexdigest()
    return checksum


def image_to_base64(image, resize_f=1.):
    """
    Converts an image to base64 encoding.

    Parameters:
        image (numpy.ndarray): The image to be converted.
        resize_f (float): The resize factor for the image (default: 1.0).

    Returns:
        str: The base64 encoded image.
    """
    _, img_base64 = cv2.imencode('.jpg', cv2.resize(image, (0,0), fx=resize_f, fy=resize_f))
    return base64.b64encode(img_base64).decode('utf-8')


class StreamPusher:
    def __init__(self, url, shape, fps):
        if fps <= 1:
            fps = 25
        if shape[0] == 0 or shape[1] == 0:
            shape = (1920, 1080)
        # 创建FFmpeg命令行参数
        ffmpeg_cmd = ['ffmpeg',                 # linux不用指定
                    '-y', '-an',
                    '-f', 'rawvideo',
                    '-vcodec','rawvideo',
                    '-pix_fmt', 'bgr24',        #像素格式
                    '-s', "{}x{}".format(shape[0], shape[1]),
                    # '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2',
                    '-r', str(fps),             # 自己的摄像头的fps是0，若用自己的notebook摄像头，设置为15、20、25都可。 
                    '-i', '-',
                    '-flush_packets', '1',
                    '-c:v', 'libx264',          # 视频编码方式
                    '-pix_fmt', 'yuv420p',
                    '-preset', 'ultrafast',
                    '-f', 'rtsp',               #  flv rtsp
                    '-rtsp_transport', 'udp',   # 使用TCP推流，linux中一定要有这行
                    url]                        # rtsp rtmp  
        # print('ffmpeg_cmd:', ffmpeg_cmd)
        # 启动 ffmpeg
        self.ffmepg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, bufsize=0)

    def push(self, frame):
        self.ffmepg_process.stdin.write(frame.tostring())
        self.ffmepg_process.stdin.flush()
    
    def close(self):
        self.ffmepg_process.kill()
    

class PlaybackHandler:
    def __init__(self, shape, fps=25, trace_time=60., out_path=config.playback_save_path, logger=logging.getLogger('PlaybackLogger')):
        self.trace_time = trace_time
        self.out_path = out_path
        self.logger = logger
        self.fps = fps
        self.shape = shape
        self.frames = SyncList()    # [(frame:cv2.Mat, time:time.time()), ...]
        self.enable_compress = True

    def check_and_pop(self):
        with self.frames._lock:
            curr_time = time.time()
            while len(self.frames._list) > 0:
                if curr_time - self.frames._list[0][1] > 2 * self.trace_time:
                    self.frames._list.pop(0)
                else:
                    break

    def put(self, frame):
        self.check_and_pop()
        frame = cv2.resize(frame.copy(), self.shape)
        _, img_encoded = cv2.imencode('.jpg', frame) if self.enable_compress else (None, frame)
        self.frames.append((img_encoded, time.time()))

    def playback(self, playback_time=time.time()):
        threading.Thread(target=self.__playback_func, args=[playback_time]).start()

    def __playback_func(self, playback_time):
        time.sleep(self.trace_time)

        self.check_and_pop()
        frame_list = self.frames.copy()
        
        save_path = os.path.join(self.out_path, f'{playback_time}.mp4')
        fps = int(len(frame_list) / (frame_list[-1][1] - frame_list[0][1]))
        writer = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, self.shape)

        for frame in frame_list:
            img_decoded = cv2.imdecode(frame[0], cv2.IMREAD_COLOR) if self.enable_compress else frame[0]
            writer.write(img_decoded)
        
        writer.release()

        self.logger.info(f'🎬 Saved playback video: {save_path}')

    @staticmethod
    def playbcak_proc_task(in_conn, shape, fps, trace_time=30., log_file=None):
        logger = logging.getLogger('PlaybackLogger')
        logger.setLevel(level = logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(processName)s - %(message)s')

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        gc_time = time.time()
        handler = PlaybackHandler(trace_time=trace_time, shape=shape, fps=fps, logger=logger)
        if log_file:
            logger.info(f'🎬 Started creating playback, shape {handler.shape}')
        
        while True:
            type, content = in_conn.get()
            if type == 0:
                handler.put(content)
            elif type == 1:
                handler.playback(content)
            
            # gc
            curr_time = time.time()
            if curr_time - gc_time > config.gc_interval:
                gc_time = curr_time
                gc.collect()


class SyncList:
    def __init__(self):
        self._list = []
        self._lock = threading.Lock()

    def append(self, item):
        with self._lock:
            self._list.append(item)

    def extend(self, items):
        with self._lock:
            self._list.extend(items)

    def remove(self, item):
        with self._lock:
            self._list.remove(item)

    def pop(self, index=-1):
        with self._lock:
            return self._list.pop(index)

    def __getitem__(self, index):
        with self._lock:
            return self._list[index]

    def __setitem__(self, index, value):
        with self._lock:
            self._list[index] = value

    def __delitem__(self, index):
        with self._lock:
            del self._list[index]

    def __len__(self):
        with self._lock:
            return len(self._list)

    def copy(self):
        with self._lock:
            return copy.deepcopy(self._list)

    def __repr__(self):
        with self._lock:
            return repr(self._list)


class BufferlessVideoCapture:
    def __init__(self, capture, logger):
        self.cap = capture
        self.logger = logger
        self.q = queue.Queue()
        t = threading.Thread(target=self._reader)
        t.daemon = True
        t.start()

    # read frames as soon as they are available, keeping only most recent one
    def _reader(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                self.logger.warning('⭕ VideoCapture failed to get frame')
                time.sleep(1.)
                continue
            if not self.q.empty():
                try:
                    self.q.get_nowait()   # discard previous (unprocessed) frame
                except queue.Empty:
                    pass
            self.q.put(frame)

    def read(self):
        return True, self.q.get(timeout=5)

    def set(self, *args):
            self.cap.set(args)

    def release(self):
            self.cap.release()


class FpsMonitor:
    def __init__(self, window_size=60, flash_interval=2.):
        self.window_size = window_size  # seconds
        self.flash_interval = flash_interval

        # 初始化Matplotlib图形
        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.fig.canvas.manager.set_window_title(f'FPS Monitor - {multiprocessing.current_process().name}')
        self.x_data = deque(maxlen=self.window_size)
        self.y_data = deque(maxlen=self.window_size)
        self.line, = self.ax.plot(self.x_data, self.y_data, label='FPS')
        self.ax.get_xaxis().set_visible(False)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        
        self.count = 0
        self.start_time = time.time()

    def flash(self):
        curr_time = time.time()
        elapsed_time = curr_time - self.start_time

        if elapsed_time > self.flash_interval:
            fps = self.count / elapsed_time

            self.count = 0
            self.start_time = curr_time

            # 更新Matplotlib图形
            self.x_data.append(curr_time)
            self.y_data.append(fps)
            self.line.set_xdata(self.x_data)
            self.line.set_ydata(self.y_data)
            self.ax.relim()
            self.ax.autoscale_view()
            # plt.text(curr_time, fps, f"{fps:.0f}", fontdict={'size':'10','color':'b'})

            # 更新图形显示
            plt.draw()
            plt.pause(0.0001)

            # print(f'⏱️ FPS: {fps:.2f}')

    def close(self):
        plt.ioff()
        # plt.show()
        plt.close()


def variance_of_laplacian(image):
    # 模糊检测：计算图像的laplacian响应的方差值
	return cv2.Laplacian(image, cv2.CV_64F).var()

def draw_text(img, text, left=0, top=0, textColor=(255, 255, 255), textSize=50):
    # 判断是否为opencv图片类型
    if (isinstance(img, np.ndarray)):
        img = Image.fromarray(img)
    draw = ImageDraw.Draw(img)
    fontText = ImageFont.truetype(properties.text_font_path, textSize, encoding="utf-8")
    linewidth = textSize + 40

    for t in text:
        draw.rectangle((left, top, left+600, top+linewidth), fill=(0,0,255), outline=(0,0,255))
        draw.text((left+20, top+20), t, textColor, font=fontText)
        top += linewidth

    return np.asarray(img)