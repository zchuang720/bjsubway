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

import utils.imgproc
import utils.net

sys.path.append("../../")
import utils
import properties
import internal.pipe.data as pipe_data
from internal.pipe.process import *


def pipe_alarm(pred_result, context, **kwargs):
    proc_name = mp.current_process().name
    ret = deepcopy(pipe_data.pipe_alarm_result)
    refine_result = deepcopy(pred_result)
    logger = logging.getLogger(context['logger_name'])

    # 修改标签类名(en => zh)
    refine_result.names = pipe_data.translated_cls_name

    # 边界坐标
    polygon = np.array(pipe_data.polygon_dict[proc_name]) if proc_name in pipe_data.polygon_dict else None
    if polygon is not None:
        for i in range(len(polygon)):
            polygon[i][0] = polygon[i][0] * pred_result.orig_shape[1]
            polygon[i][1] = polygon[i][1] * pred_result.orig_shape[0]
        polygon.astype(np.int32)

    display_info = []       # 画面左上角警报信息
    alarm_event_id = []     # 警报事件编号
    post_time = time.time()

    # 检测警报事件
    if polygon is not None:
        filter_outbounding_target(refine_result, polygon)
    
    if check_anchor_state(refine_result) or check_pipe_state(refine_result):
        alarm_event_id.append(4)    # 4.明挖支护-超时未支护

    # add process name
    display_info.insert(0, f"{context['post_data']['name'].split('-')[-1]}路")
    
    # 生成左上角警报信息
    for id in alarm_event_id:
        if id == 4:
            display_info.append("钢支撑未支护")
    
    ret["refine_result"] = refine_result
    ret["display_info"] = display_info
    ret["need_post"] = False
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

        alarm_image = pipe_plot(pred_result.orig_img, ret)
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
        camera_alarm_data["md5Check"] = utils.net.generate_md5_checksum(camera_alarm_data["equipmentId"] 
                                                                   + camera_alarm_data["time"] 
                                                                   + camera_alarm_data["alarmType"] + properties.md5_salt)
        post_data["data"].append(camera_alarm_data)
        
        logger.info(f'📨 {post_data}')

        camera_alarm_data["alarmImage"] = utils.imgproc.image_to_base64(alarm_image, resize_f=1.)
        utils.net.post(properties.post_addr, post_data, logger=logger)
        
    return ret


def pipe_plot(img, alarm_result, **kwargs):
    img_ret = deepcopy(img)
    # 画边界框
    if 'polygon' in alarm_result and alarm_result['polygon'] is not None:
        img_ret = cv2.polylines(img_ret, [alarm_result['polygon'].astype(np.int32)], isClosed=True, color=(255,0,0), thickness=3)
    # 画目标框
    if 'refine_result' in alarm_result:
        img_ret = alarm_result['refine_result'].plot(img=img_ret, conf=False)
    # 画警报信息
    if 'display_info' in alarm_result:
        img_ret = draw_text(img_ret, alarm_result['display_info'])
    return img_ret
