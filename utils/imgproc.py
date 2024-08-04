import base64
import queue
import threading
import time

import cv2

from PIL import Image, ImageDraw, ImageFont
import numpy as np

import properties


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


# 判断类别缓冲函数装饰器，用于减轻结果波动
def yolo_cls_buff(size=3):
    def decorator(func):
        has_cls = False
        cnt = 0
        def wrapper(*args, **kwargs):
            nonlocal has_cls, cnt
            ret = func(*args, **kwargs)
            if ret:
                cnt = min(cnt + 1, size)
            else:
                cnt = max(0, cnt - 1)
            if not has_cls and cnt == size:
                has_cls = True
            elif has_cls and cnt == 0:
                has_cls = False
            return has_cls
        return wrapper
    return decorator