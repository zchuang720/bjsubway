import cv2
import numpy as np
import time
from PIL import Image, ImageDraw, ImageFont

import properties
from models.tunnel.data import *
from utils.imgproc import yolo_cls_buff

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


def update_event_duration(context, exclusion_id, event_id):
    """
    更新事件持续时间记录，返回事件持续时间
    key: event_id
    value: event_start_time
    return: event_duration = now_time - event_start_time
    """
    exclusion_key = f"event_exclusion_{exclusion_id}"
    if exclusion_key not in context:
        context[exclusion_key] = {}

    event_dict = context[exclusion_key]
    if event_id not in event_dict:
        event_dict[event_id] = 0

    now = time.time()
    for key in event_dict:
        if key == event_id:
            if event_dict[key] == 0:
                event_dict[key] = now
        else:
            event_dict[key] = 0
    
    return now - event_dict[event_id]


def get_event_duration(context, exclusion_id, event_id):
    # 获取事件持续时间，未发生则返回 0
    exclusion_key = f"event_exclusion_{exclusion_id}"
    if exclusion_key not in context:
        context[exclusion_key] = {}

    event_dict = context[exclusion_key]
    if event_id not in event_dict:
        event_dict[event_id] = 0

    if event_dict[event_id] == 0:
        return 0
    else:
        return time.time() - event_dict[event_id]


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

