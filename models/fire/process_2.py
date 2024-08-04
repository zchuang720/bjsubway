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

sys.path.append("../../")
import utils
import data
import models.fire.data as fire_data


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


def check_fire_state(pred_result):
    # 判断是否有动火人(2)
    return 2 in pred_result.boxes.cls

def check_watcher_state(pred_result):
    # 判断是否有看火人(3)
    return 3 in pred_result.boxes.cls

def check_fire_state(pred_result):
    # 判断是否动火，即是否有明火(4)
    return 4 in pred_result.boxes.cls

def check_extinguisher_state(pred_result):
    # 判断是否有灭火器(5)
    return 5 in pred_result.boxes.cls

def check_bucket_state(pred_result):
    # 判断是否有消防桶(6)
    return 6 in pred_result.boxes.cls

def calc_2_point_dist(p1, p2):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

def check_fire_operator_state(pred_result):
    # 判断动火人与明火
    has_fire = check_fire_state(pred_result)
    if not has_fire:
        # 没有动火，则把类别2的动火人(正在动火)改为类别1(未动火)
        for i in range(len(pred_result.boxes.data)):
            if pred_result.boxes.data[i][-1] == 2:
                pred_result.boxes.data[i][-1] = 1
        return 0    # 没有动火
    else:
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
            if pred_result.boxes.data[i][-1] == 2:
                xyxy = pred_result.boxes.data[i][0:4]
                person_pos = ((xyxy[0] + xyxy[2]) / 2, (xyxy[1] + xyxy[3]) / 2)
                for j in range(len(fire_pos)):
                    if calc_2_point_dist(person_pos, fire_pos[j]) < dist_threshold:
                        true_operator_cnt += 1
                        break
                    else:
                        pred_result.boxes.data[i][-1] = 1   # 大于阈值改为类别1(未动火)
        
        if true_operator_cnt == 0:  # 如果没有有效动火人，则返回-1
            return -1
        elif true_operator_cnt == 1:  # 如果只有一个有效动火人，则返回1
            return 1
        elif true_operator_cnt > 1:  # 如果有多个有效动火人，则返回2
            return 2

def draw_text(img, text, left=0, top=0, textColor=(255, 255, 255), textSize=60):
    # 判断是否为opencv图片类型
    if (isinstance(img, np.ndarray)):
        img = Image.fromarray(img)
    draw = ImageDraw.Draw(img)
    fontText = ImageFont.truetype(data.text_font_path, textSize, encoding="utf-8")
    linewidth = textSize + 40

    for t in text:
        draw.rectangle((left, top, left+600, top+linewidth), fill=(0,0,255), outline=(0,0,255))
        draw.text((left+20, top+20), t, textColor, font=fontText)
        top += linewidth

    return np.asarray(img)

