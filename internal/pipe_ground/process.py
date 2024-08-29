from itertools import combinations
import math
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
import properties
from internal.pipe_ground.data import *


def filter_outbounding_target(pred_result, polygon):
    boxes = pred_result.boxes.data.cpu()

    # 找出不在边界内的目标
    outbounding_target_list = []
    bounding_dist_threshold = int(bounding_dist_threshold * pred_result.orig_shape[0])
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


# 根据类别进行分组, 返回 dict{class: [[bbox], [mask]]}
def grep_results_by_class(pred_result):
    n_class = len(pred_result.names)
    has_mask = hasattr(pred_result, 'masks')

    grep_results = {}
    for i in range(n_class):
        grep_results[i] = [[],[]]   # [[bbox], [mask]]

    boxes_data = pred_result.boxes.data.cpu()
    if has_mask:
        mask_data = pred_result.masks.cpu().xy

    for i in range(len(boxes_data)):
        cls = int(boxes_data[i][-1])
        grep_results[cls][0].append(boxes_data[i][0:4])
        if has_mask:
            grep_results[cls][1].append(mask_data[i])

    return grep_results


# 找出距离安装好的钢管最近的托盘
def find_anchor_adjacent_installed_pipe(grep_results):
    anchor_center = [(int((i[0] + i[2]) / 2), int((i[1] + i[3]) / 2)) for i in grep_results[id_anchor][0]]
    installed_pipe_center = [(int((i[0] + i[2]) / 2), int((i[1] + i[3]) / 2)) for i in grep_results[id_installed_pipe][0]]
    nearest_dist = 999999
    nearest_idx = -1

    for i in range(len(installed_pipe_center)):
        for j in range(len(anchor_center)):
            dist = calc_2_point_dist(installed_pipe_center[i], anchor_center[j])
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_idx = i

    return nearest_idx


# 检索附近有反压土的托盘
def find_anchor_near_ground(grep_results):
    anchor_list = []
    for i in range(len(grep_results[id_anchor][0])):
        anchor_xyxy = grep_results[id_anchor][0][i]
        anchor_edgelen = abs(int((anchor_xyxy[0] - anchor_xyxy[2] + anchor_xyxy[1] - anchor_xyxy[3]) / 2))
        anchor_downside_center = (int((anchor_xyxy[0] + anchor_xyxy[2]) / 2),
                                int((anchor_xyxy[1] + anchor_xyxy[3]) / 2))
        min_dist = 1e10
        for j in grep_results[id_ground][1]:
            dist = - cv2.pointPolygonTest(np.array(j, dtype=np.float32), anchor_downside_center, True)
            min_dist = min(min_dist, dist)
        if min_dist > anchor_edgelen * 2:
            anchor_list.append(i)
    return anchor_list


# 判断第idx个托盘附近是否有反压土
def check_anchor_is_near_ground(grep_results, anchor_idx):
    anchor_xyxy = grep_results[id_anchor][0][anchor_idx]
    anchor_edgelen = abs(int((anchor_xyxy[0] - anchor_xyxy[2] + anchor_xyxy[1] - anchor_xyxy[3]) / 2))
    anchor_downside_center = (int((anchor_xyxy[0] + anchor_xyxy[2]) / 2),
                              int((anchor_xyxy[1] + anchor_xyxy[3]) / 2 + anchor_edgelen * 1.5))
    for i in grep_results[id_ground][1]:
        dist = cv2.pointPolygonTest(np.array(i, dtype=np.float32), anchor_downside_center, True)
        if dist < anchor_edgelen * 0.5:
            return True
    return False


def check_anchor_similarity(anchor1, anchor2):
    anchor1_centor = (int((anchor1[0] + anchor1[2]) / 2), int((anchor1[1] + anchor1[3]) / 2))
    anchor2_centor = (int((anchor2[0] + anchor2[2]) / 2), int((anchor2[1] + anchor2[3]) / 2))
    anchor1_edgelen = abs(int((anchor1[0] - anchor1[2] + anchor1[1] - anchor1[3]) / 2))
    anchor2_edgelen = abs(int((anchor2[0] - anchor2[2] + anchor2[1] - anchor2[3]) / 2))
    dist = calc_2_point_dist(anchor1_centor, anchor2_centor)
    # 判断边长相似性和距离相似性
    return dist < (anchor1_edgelen + anchor2_edgelen) / 2


# 匹配和过滤当前目标和历史目标
def check_pair_match_history(context, target_anchor_xyxy_list):
    rcd_center = [(int((i[0] + i[2]) / 2), int((i[1] + i[3]) / 2)) for i in context['target_anchor_xyxy']]
    curr_center = [(int((i[0] + i[2]) / 2), int((i[1] + i[3]) / 2)) for i in target_anchor_xyxy_list]
    match_pairs = match_points(rcd_center, curr_center)
    val_pairs = []
    for pair in match_pairs:
        idx1, idx2, dist = pair
        box1 = context['target_anchor_xyxy'][idx1]
        box2 = target_anchor_xyxy_list[idx2]
        avg_edgelen = abs(int((box1[0] - box1[2] + box1[1] - box1[3] + box2[0] - box2[2] + box2[1] - box2[3]) / 4))
        if dist < avg_edgelen:
            val_pairs.append(pair)
    return val_pairs


# 更新历史目标记录
def update_history(context, pairs, curr_xyxy_list):
    rcd_xyxy_list = context['target_anchor_xyxy']
    rcd_cnt_list = context['target_anchor_cnt']
    rcd_matched = []
    curr_matched = []
    rcd_remove = []

    if pairs is not None and curr_xyxy_list is not None:
        # 更新匹配的记录
        for pair in pairs:
            idx1, idx2, _ = pair
            rcd_matched.append(idx1)
            curr_matched.append(idx2)
            rcd_xyxy_list[idx1] = (rcd_xyxy_list[idx1] + curr_xyxy_list[idx2]) / 2
            rcd_cnt_list[idx1] = min(rcd_cnt_list[idx1] + 1, timer_duration)
        # 添加新记录
        curr_mismatched = [i for i in range(len(curr_xyxy_list)) if i not in curr_matched]
        for i in curr_mismatched:
            rcd_xyxy_list.append(curr_xyxy_list[i])
            rcd_cnt_list.append(1)
    
    # 未匹配记录次数减一
    for i in range(len(rcd_xyxy_list)):
        if i not in rcd_matched:
            rcd_cnt_list[i] = rcd_cnt_list[i] - 1
            if rcd_cnt_list[i] < 0:
                rcd_remove.append(i)
    # 删除过期记录
    for i in range(len(rcd_remove)-1, -1, -1):
        rcd_xyxy_list.pop(rcd_remove[i])
        rcd_cnt_list.pop(rcd_remove[i])
    # 记录过多时循环删除次数最少的记录
    while len(rcd_xyxy_list) > 10:
        rm_idx = rcd_cnt_list.index(min(rcd_cnt_list))
        rcd_xyxy_list.pop(rm_idx)
        rcd_cnt_list.pop(rm_idx)


def check_has_anchor(gred_result):
    # 判断是否有未安装的底座
    return len(gred_result[id_anchor][0]) > 0

def check_has_installed_pipe(gred_result):
    # 判断是否有安装好的钢管
    return len(gred_result[id_installed_pipe][0]) > 0

def check_has_ground(gred_result):
    # 判断是否有反压土
    return len(gred_result[id_ground][0]) > 0

def check_has_pipe_bottom(gred_result):
    # 判断是否有未安装的钢管
    return len(gred_result[id_pipe_bottom][0]) > 0


def calc_2_point_dist(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def find_closest_pairs(points):
    pairs = []
    while points:
        min_distance = float('inf')
        closest_pair = None
        
        # Generate all possible pairs and find the closest one
        for pair in combinations(points, 2):
            dist = calc_2_point_dist(pair[0], pair[1])
            if dist < min_distance:
                min_distance = dist
                closest_pair = pair
        
        pairs.append(closest_pair)
        points.remove(closest_pair[0])
        points.remove(closest_pair[1])
    
    return pairs


from scipy.spatial import distance_matrix
from scipy.optimize import linear_sum_assignment

# 按最小距离匹配两个点集
def match_points(A, B):
    # Calculate the distance matrix
    dist_matrix = distance_matrix(A, B)
    # Use the Hungarian algorithm to find the minimum cost matching
    row_ind, col_ind = linear_sum_assignment(dist_matrix)
    res = []
    for i, j in zip(row_ind, col_ind):
        res.append((i, j, dist_matrix[i, j]))
    return res


def draw_text(img, text, left=0, top=0, textColor=(255, 255, 255), textSize=60):
    # 判断是否为opencv图片类型
    if (isinstance(img, np.ndarray)):
        img = Image.fromarray(img)
    draw = ImageDraw.Draw(img)
    fontText = ImageFont.truetype(properties.text_font_path, textSize, encoding="utf-8")
    linewidth = textSize + 40

    for t in text:
        draw.rectangle((left, top, left+400, top+linewidth), fill=(0,0,255), outline=(0,0,255))
        draw.text((left+20, top+20), t, textColor, font=fontText)
        top += linewidth

    return np.asarray(img)