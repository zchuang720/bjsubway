import os
import sys
import cv2
import copy
import threading
import time
import logging
import numpy as np
import multiprocessing as mp
from copy import deepcopy
from ultralytics import YOLO

sys.path.append("../../")
import util
import properties
import models.pipe_ground.data as pipe_data
from models.pipe_ground.process import *


def pipe_alarm(pred_result, context, **kwargs):
    proc_name = mp.current_process().name
    ret = deepcopy(pipe_data.pipe_alarm_result)
    refine_result = deepcopy(pred_result)
    logger = logging.getLogger(context['logger_name'])
    if 'target_anchor_xyxy' not in context:
        context['target_anchor_xyxy'] = []
        context['target_anchor_cnt'] = []

    # 修改标签类名(en => zh)
    refine_result.names = pipe_data.translated_cls_name

    # 边界坐标
    polygon = np.array(pipe_data.polygon_dict[proc_name]) if proc_name in pipe_data.polygon_dict else None
    if polygon is not None:
        for i in range(len(polygon)):
            polygon[i][0] = polygon[i][0] * refine_result.orig_shape[1]
            polygon[i][1] = polygon[i][1] * refine_result.orig_shape[0]
        polygon.astype(np.int32)
    
    if polygon is not None:
        filter_outbounding_target(refine_result, polygon)

    display_info = []       # 画面左上角警报信息
    alarm_event_id = []     # 警报事件编号
    post_time = time.time()
    grep_results = grep_results_by_class(refine_result)

    need_update_history = True

    # 场景内有反压土时
    if check_has_ground(grep_results):
        # 检查是否有托盘
        if check_has_anchor(grep_results):
            # 检索反压土附近的托盘
            target_anchor_idx_list = find_anchor_near_ground(grep_results)
            # 若存在反压土附近的托盘
            if len(target_anchor_idx_list) > 0:
                target_anchor_xyxy_list = [grep_results[id_anchor][0][i] for i in target_anchor_idx_list]
                # 检查历史目标托盘
                if len(context['target_anchor_xyxy']) == 0:
                    # 新增记录
                    context['target_anchor_xyxy'] = target_anchor_xyxy_list
                    context['target_anchor_cnt'] = [1] * len(target_anchor_xyxy_list)
                else:
                    # 检查历史相似性
                    pairs = check_pair_match_history(context, target_anchor_xyxy_list)
                    # 更新历史记录
                    update_history(context, pairs, target_anchor_xyxy_list)
                    need_update_history = False
                    # 有效目标则报警
                    max_cnt = max(context['target_anchor_cnt'])
                    if max_cnt >= 60:
                        alarm_event_id.append(4)    # 4.明挖支护-超时未支护


        """ 按架设顺序报警逻辑
        # 有安装好的钢管时
        if check_has_installed_pipe(grep_results):
            # 找到距离安装好的钢管最近的托盘
            anchor_idx = find_anchor_adjacent_installed_pipe(grep_results)
            # 检测托盘是否靠近反压土
            is_near_ground = True
            # is_near_ground = check_anchor_is_near_ground(grep_results, anchor_idx)
            if is_near_ground:
                # 检查原始目标托盘
                if context['target_anchor'] is None:
                    # 新增目标托盘
                    context['target_anchor'] = grep_results[id_anchor][0][anchor_idx]
                else:
                    # 检查相似性
                    if check_anchor_similarity(context['target_anchor'], grep_results[id_anchor][0][anchor_idx]):
                        alarm_event_id.append(4)    # 4.明挖支护-超时未支护
                        context['target_anchor_update_time'] = post_time
                    else:
                        context['target_anchor_update_time'] = post_time
                    context['target_anchor'] = grep_results[id_anchor][0][anchor_idx]
            else:
                pass
            
        else:
            pass
        """

    # 场景内无反压土时
    else:
        # 检测警报事件
        if check_has_anchor(refine_result) or check_has_pipe_bottom(refine_result):
            alarm_event_id.append(4)    # 4.明挖支护-超时未支护
    
    if need_update_history:
        update_history(context, None, None)
    print(context['target_anchor_cnt'])

    # add process name
    if context['post_data']['name'] != "":
        display_info.insert(0, f"{context['post_data']['name'].split('-')[-1]}路")
    
    # 生成左上角警报信息
    for id in alarm_event_id:
        if id == 4:
            display_info.append("钢支撑未支护")
    
    ret["refine_result"] = refine_result
    ret["display_info"] = display_info
    ret["need_post"] = False
    ret['target_anchor_xyxy'] = context['target_anchor_xyxy']
    ret['target_anchor_cnt'] = context['target_anchor_cnt']
    if polygon is not None:
        ret["polygon"] = polygon

    # 发送警报post
    need_post = False
    if len(alarm_event_id) > 0:
        if 'post_alarm_event_id' not in context:
            context['post_alarm_event_id'] = {}
            
        for id in alarm_event_id:
            if id not in context['post_alarm_event_id'] or \
                        post_time - context['post_alarm_event_id'][id] > properties.post_time_interval['pipe']:
                context['post_alarm_event_id'][id] = post_time
                need_post = True
    
    if need_post:
        ret["need_post"] = True
        ret['post_time'] = post_time

        logger.info(display_info)
        context['post_time'] = post_time
        # context['post_alarm_event_id'] = alarm_event_id

        alarm_image = pipe_plot(refine_result.orig_img, ret)
        cv2.imwrite(f"{properties.alarm_image_save_path}/pipe-{post_time}.jpg", alarm_image)
        cv2.imwrite(f"{properties.alarm_image_save_path}/pipe-{post_time}_orig.jpg", pred_result.orig_img)

        post_data = copy.deepcopy(properties.post_data_dict)
        post_data["equipment_type"] = "camera"
        post_data["event_type"] = "alarm"

        camera_alarm_data = copy.deepcopy(properties.camera_alarm_data_dict)
        camera_alarm_data["model"] = "2"
        camera_alarm_data["brand"] = "bjtu"
        camera_alarm_data["equipmentId"] = "pipe_alarm_1"
        camera_alarm_data["alarmType"] = str(alarm_event_id[0])
        camera_alarm_data["alarmUrl"] = f'{properties.playback_url}/{post_time}'
        camera_alarm_data["name"] = "Pipe alarm 1"
        camera_alarm_data["time"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        camera_alarm_data["gongdiSN"] = properties.gongdiSN
        camera_alarm_data["latitude"] = ""
        camera_alarm_data["longitude"] = ""
        camera_alarm_data["alarmInfo"] = ""

        if 'post_data' in context and context['post_data'] is not None:
            camera_alarm_data.update(context['post_data'])
        camera_alarm_data["md5Check"] = util.generate_md5_checksum(camera_alarm_data["equipmentId"] 
                                                                   + camera_alarm_data["time"] 
                                                                   + camera_alarm_data["alarmType"] + properties.md5_salt)
        post_data["data"].append(camera_alarm_data)
        
        logger.info(f'📨 {post_data}')

        camera_alarm_data["alarmImage"] = util.image_to_base64(alarm_image, resize_f=1.)
        # util.post(properties.post_addr, post_data, logger=logger)
        
    return ret


def pipe_plot(img, alarm_result, **kwargs):
    img_ret = deepcopy(img)
    # 画边界框
    if 'polygon' in alarm_result and alarm_result['polygon'] is not None:
        img_ret = cv2.polylines(img_ret, [alarm_result['polygon'].astype(np.int32)], isClosed=True, color=(255,0,0), thickness=3)
    # 画目标框
    if 'refine_result' in alarm_result:
        img_ret = alarm_result['refine_result'].plot(img=img_ret, conf=False)
    if 'target_anchor_xyxy' in alarm_result:
        target_anchor_cnt = alarm_result['target_anchor_cnt']
        for i, anchor in enumerate(alarm_result['target_anchor_xyxy']):
            pt1, pt2 = (int(anchor[0]), int(anchor[1])), (int(anchor[2]), int(anchor[3]))
            cv2.rectangle(img_ret, pt1, pt2, color=(0,255,255), thickness=3)
            cv2.putText(img_ret, f"{target_anchor_cnt[i]}", pt2, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
    # 画警报信息
    if 'display_info' in alarm_result:
        img_ret = draw_text(img_ret, alarm_result['display_info'])
    return img_ret
