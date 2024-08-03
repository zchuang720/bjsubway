import cv2
import numpy as np
import time
from PIL import Image, ImageDraw, ImageFont

import properties
from models.tunnel.data import *

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

@yolo_cls_buff(yolo_cls_buff_size)
def check_has_person(pred_result):
    # 判断是否有人
    return id_person in pred_result.boxes.cls

@yolo_cls_buff(yolo_cls_buff_size)
def check_has_steel(pred_result):
    # 判断是否有钢架
    return id_steel in pred_result.boxes.cls

@yolo_cls_buff(yolo_cls_buff_size)
def check_has_woking_face(pred_result):
    # 判断是否有开挖面
    return id_working_face in pred_result.boxes.cls

@yolo_cls_buff(yolo_cls_buff_size)
def check_has_truck(pred_result):
    # 判断是否有卡车
    return id_truck in pred_result.boxes.cls


def update_event_duration(context, event_id, if_happen):
    event_key = f"event_start_time_{event_id}"
    if event_key not in context:
        context[event_key] = 0

    now_time = time.time()
    if if_happen and context[event_key] == 0:
        context[event_key] = now_time
    elif not if_happen and context[event_key] != 0:
        context[event_key] = 0
        return 0

    return now_time - context[event_key]


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

