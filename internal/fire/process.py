import os
import sys
import cv2
import copy
import threading
import time
import numpy as np
from copy import deepcopy
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO
from ultralytics.engine.results import Boxes, Results
from ultralytics.engine import predictor

from utils.imgproc import yolo_cls_buff

sys.path.append("../../")
import utils
import properties
import internal.fire.data as fire_data


def filter_outbounding_target(pred_result, polygon):
    boxes = pred_result.boxes.data.cpu()

    # 找出不在边界内的目标
    outbounding_target_list = []
    bounding_dist_threshold = int(fire_data.bounding_dist_threshold * pred_result.orig_shape[0])
    for i in range(len(pred_result)):
        xyxy = boxes[i][0:4]
        center = (int((xyxy[0] + xyxy[2]) / 2), int((xyxy[1] + xyxy[3]) / 2))
        # 如果measureDist = False，如果点在轮廓内则返回+1，如果在轮廓边界上返回0，如果在轮廓外返回-1。* 如果 measureDist = True，则返回点与轮廓之间的距离。如果点在轮廓内，则返回正值，如果在轮廓的边界上，则返回 0，如果点在轮廓外，则返回负值。
        is_in_polygon = cv2.pointPolygonTest(polygon.astype(np.float32), center, True)
        if is_in_polygon < - bounding_dist_threshold:
            outbounding_target_list.append(i)
    # 构造新的boxes替换到pred_result中
    filter_boxes = np.delete(boxes, outbounding_target_list, axis=0)
    pred_result.boxes = Boxes(filter_boxes, pred_result.orig_shape)


# @yolo_cls_buff(fire_data.yolo_cls_buff_size)
def check_has_operator(pred_result):
    # 判断是否有动火人(2)
    return 2 in pred_result.boxes.cls

# @yolo_cls_buff(fire_data.yolo_cls_buff_size)
def check_has_watcher(pred_result):
    # 判断是否有看火人(3)
    return 3 in pred_result.boxes.cls

# @yolo_cls_buff(fire_data.yolo_cls_buff_size)
def check_has_fire(pred_result):
    # 判断是否动火，即是否有明火(4)
    return 4 in pred_result.boxes.cls

# @yolo_cls_buff(fire_data.yolo_cls_buff_size)
def check_has_extinguisher(pred_result):
    # 判断是否有灭火器(5)
    return 5 in pred_result.boxes.cls

# @yolo_cls_buff(fire_data.yolo_cls_buff_size)
def check_has_bucket(pred_result):
    # 判断是否有消防桶(6)
    return 6 in pred_result.boxes.cls

def assert_has_fire(pred_result):
    # 判断是否有明火(4), 不走缓冲
    return 4 in pred_result.boxes.cls

def calc_2_point_dist(p1, p2):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

def smoother(buff_size=3):
    def _smoother(func):
        buff = [0] * buff_size
        ptr = 0
        res = 0
        def __smoother(*args, **kwargs):
            nonlocal ptr, res
            buff[ptr] = func(*args, **kwargs)
            ptr = (ptr + 1) % buff_size
            if len(set(buff)) == 1:
                res = buff[0]
            return res
        return __smoother
    return _smoother

# @smoother(buff_size=2)      # 加了之后会出现识别出动火人但是由于缓冲为非而发出非特种工动火
def check_fire_operator_state(pred_result, has_fire):
    if not has_fire:
        # 没有动火，则把类别2的动火人(正在动火)改为类别1(未动火)
        for i in range(len(pred_result.boxes.data)):
            if pred_result.boxes.data[i][-1] == 2:
                pred_result.boxes.data[i][-1] = 1
        return 0
    
    # 有动火，则计算动火人离明火的距离，小于阈值的标为的动火人
    dist_threshold = pred_result.orig_shape[0] * fire_data.dist_fire_operator_threshold
    true_operator_cnt = 0   # 有效动火人的数量
    # 找到火源位置
    fire_pos = []
    for i in range(len(pred_result.boxes.data)):
        if pred_result.boxes.data[i][-1] == 4:
            xyxy = pred_result.boxes.data[i][0:4]
            fire_pos.append(((xyxy[0] + xyxy[2]) / 2, (xyxy[1] + xyxy[3]) / 2))
    # 遍历动火人计算距离
    for i in range(len(pred_result.boxes.data)):
        cls = pred_result.boxes.data[i][-1]
        if cls == 2 or cls == 1:
            xyxy = pred_result.boxes.data[i][0:4]
            person_pos = ((xyxy[0] + xyxy[2]) / 2, (xyxy[1] + xyxy[3]) / 2)
            for j in range(len(fire_pos)):
                if calc_2_point_dist(person_pos, fire_pos[j]) < dist_threshold:
                    pred_result.boxes.data[i][-1] = 2
                    true_operator_cnt += 1
                    break
                else:
                    pred_result.boxes.data[i][-1] = 1   # 大于阈值改为类别1(未动火)
    # 如果没有有效动火人，则返回-1
    if true_operator_cnt == 0:
        return -1
    else:
        return true_operator_cnt

def draw_text(img, text, left=0, top=0, textColor=(255, 255, 255), textSize=60):
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
