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
import  models.tunnel.data as tunnel_data
from models.tunnel.process import *


def grid_alarm(pred_result, context, **kwargs):
    ret = deepcopy(tunnel_data.grid_alarm_result)
    refine_result = deepcopy(pred_result)
    logger = logging.getLogger(context['logger_name'])

    # 修改标签类名(en => zh)
    refine_result.names = tunnel_data.translated_cls_name

    display_info = []       # 画面左上角警报信息
    alarm_event_id = []     # 警报事件编号
    post_time = time.time()

    # TODO: 检测警报事件
    event_id = 999
    # 有开挖面
    if check_has_woking_face(refine_result):
        during = update_event_duration(context, event_id=event_finish_dig, if_happen=True)
        if during > event_timeout[event_finish_dig]:
            event_id = min(event_id, event_finish_dig)
            alarm_event_id.append(19)
    # 无开挖面
    else:
        update_event_duration(context, event_id=event_finish_dig, if_happen=False)
        event_id = min(event_id, event_doing_dig)

    # 有卡车
    if check_has_truck(refine_result):
        event_id = min(event_id, event_doing_dig)
        update_event_duration(context, event_id=event_doing_dig, if_happen=False)
    # 无卡车
    else:
        during = update_event_duration(context, event_id=event_doing_dig, if_happen=True)
        # 小于 2 小时 (暂定)
        if during < event_timeout[event_doing_dig]:
            event_id = min(event_id, event_finish_dig)
        # 大于 2 小时
        else:
            # 有人
            if check_has_person(refine_result):
                event_id = min(event_id, event_stop_working)
                update_event_duration(context, event_id=event_finish_dig, if_happen=False)
            # 无人
            else:
                event_id = min(event_id, event_finish_dig)
                during = update_event_duration(context, event_id=event_finish_dig, if_happen=True)
                # 大于 y 小时
                if during > event_timeout[event_finish_dig]:
                    event_id = min(event_id, event_stop_working)
                    alarm_event_id.append(18)


    """
    if check_steel_state(refine_result):
        alarm_event_id.append(18)   # 18.暗挖未及时喷射混凝土
    if check_woking_face_state(refine_result):
        alarm_event_id.append(19)   # 19.暗挖未及时架设钢支撑（待定）

    # add process name
    display_info.insert(0, f"{context['post_data']['name'].split('-')[-1]}路")
    """

    # 生成左上角警报信息
    for id in alarm_event_id:
        if id == 18:
            # display_info.append("未喷射混凝土")
            pass
        if id == 19:
            display_info.append("未架设钢格栅")
    
    ret["refine_result"] = refine_result
    ret["display_info"] = display_info
    ret["need_post"] = False

    # 发送警报post
    need_post = False
    if len(alarm_event_id) > 0:
        if 'post_alarm_event_id' not in context:
            context['post_alarm_event_id'] = {}
            
        for id in alarm_event_id:
            if id not in context['post_alarm_event_id'] or \
                        post_time - context['post_alarm_event_id'][id] > properties.post_time_interval['grid']:
                context['post_alarm_event_id'][id] = post_time
                need_post = True
    
    if need_post:
        ret["need_post"] = True
        ret['post_time'] = post_time

        logger.info(display_info)
        context['post_time'] = post_time
        # context['post_alarm_event_id'] = alarm_event_id

        alarm_image = grid_plot(pred_result.orig_img, ret)
        cv2.imwrite(f"{properties.alarm_image_save_path}/pipe-{post_time}.jpg", alarm_image)

        post_data = copy.deepcopy(properties.post_data_dict)
        post_data["equipment_type"] = "camera"
        post_data["event_type"] = "alarm"

        camera_alarm_data = copy.deepcopy(properties.camera_alarm_data_dict)
        camera_alarm_data["model"] = "2"
        camera_alarm_data["brand"] = "brand"
        camera_alarm_data["equipmentId"] = "equipmentId"
        camera_alarm_data["alarmType"] = str(alarm_event_id[0])
        camera_alarm_data["alarmUrl"] = f'{properties.playback_url}/{post_time}'
        camera_alarm_data["name"] = "name"
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
        util.post(properties.post_addr, post_data, logger=logger)

    return ret


def grid_plot(img, alarm_result, **kwargs):
    img_ret = deepcopy(img)
    # 画边界框
    if 'polygon' in alarm_result:
        img_ret = cv2.polylines(img_ret, [alarm_result['polygon'].astype(np.int32)], isClosed=True, color=(255,0,0), thickness=3)
    # 画目标框
    if 'refine_result' in alarm_result:
        img_ret = alarm_result['refine_result'].plot(img=img_ret, conf=False)
        # boxes = alarm_result['refine_result'].boxes.xyxy.cpu().numpy().astype(np.int32)
        # centers = np.array([[(boxes[i][0] + boxes[i][2]) / 2, (boxes[i][1] + boxes[i][3]) / 2]
        #                         for i in range(len(boxes))]).astype(np.int32)
        # for center in centers:
        #     cv2.circle(img_ret, center, 3, (0,255,0), 3)
    # 画警报信息
    if 'display_info' in alarm_result:
        img_ret = draw_text(img_ret, alarm_result['display_info'])
    return img_ret
