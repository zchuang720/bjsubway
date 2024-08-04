
import copy
import gc
import logging
import os
import threading
import time

import cv2

import config


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

