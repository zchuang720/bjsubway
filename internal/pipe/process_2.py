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

sys.path.append("../../")
import utils
import data
import internal.pipe.data as pipe_data


def filter_outbounding_target(pred_result, polygon):
    boxes = pred_result.boxes.data.cpu()

    # 找出不在边界内的目标
    outbounding_target_list = []
    bounding_dist_threshold = int(pipe_data.bounding_dist_threshold * pred_result.orig_shape[0])
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


def check_anchor_state(pred_result):
    # 判断是否有未安装的底座
    return 0 in pred_result.boxes.cls

def check_uninstalled_pipe_state(pred_result):
    # 判断是否有未安装的钢管
    return 2 in pred_result.boxes.cls

def check_installed_pipe_state(pred_result):
    # 判断是否有安装好的钢管
    return 1 in pred_result.boxes.cls


def draw_text(img, text, left=0, top=0, textColor=(255, 255, 255), textSize=60):
    # 判断是否为opencv图片类型
    if (isinstance(img, np.ndarray)):
        img = Image.fromarray(img)
    draw = ImageDraw.Draw(img)
    fontText = ImageFont.truetype(data.text_font_path, textSize, encoding="utf-8")
    linewidth = textSize + 40

    for t in text:
        draw.rectangle((left, top, left+400, top+linewidth), fill=(0,0,255), outline=(0,0,255))
        draw.text((left+20, top+20), t, textColor, font=fontText)
        top += linewidth

    return np.asarray(img)

