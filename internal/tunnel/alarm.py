import sys
import cv2
import copy
import time
import logging
import numpy as np
from copy import deepcopy

import utils.imgproc

sys.path.append("../../")
import utils
import properties
import  internal.tunnel.data as tunnel_data
from internal.tunnel.process import *


def tunnel_alarm(pred_result, context, **kwargs):
    ret = deepcopy(tunnel_data.grid_alarm_result)
    refine_result = deepcopy(pred_result)
    logger = logging.getLogger(context['logger_name'])

    # 修改标签类名(en => zh)
    refine_result.names = tunnel_data.translated_cls_name

    display_info = []       # 画面左上角警报信息
    alarm_event_id = []     # 警报事件编号
    post_time = time.time()

    # 事件1 开挖面是否存在超过一定时间
    event_id1 = -1
    # 有开挖面
    if check_has_working_face(refine_result):
        event_id1 = Event.hasHole
    # 无开挖面
    else:
        event_id1 = Event.noHole
    update_event_duration(context, 1, event_id1)

    # 事件2 卡车是否存在超过一定时间且有人
    event_id2 = -1
    event_id3 = -1
    # 有卡车->正在挖
    if check_has_truck(refine_result):
        event_id2 = Event.hasCar
        event_id3 = Event.noCar_aboveThresh_noPerson
    # 无卡车
    else:
        event_id2 = Event.noCar
        # 小于 x 小时 (暂定)->没挖完
        if get_event_duration(context, 2, Event.noCar) < event_timeout[Event.noCar]:
            event_id3 = Event.noCar_aboveThresh_noPerson
        # 大于 x 小时
        else:
            # 有人->挖完了
            if check_has_person(refine_result):
                event_id3 = Event.noCar_aboveThresh_hasPerson
            # 无人->停工了
            else:
                event_id3 = Event.noCar_aboveThresh_noPerson
    update_event_duration(context, 2, event_id2)
    update_event_duration(context, 3, event_id3)

    # 事件3 格栅不存在超过一定时间且有人
    event_id4 = -1
    event_id5 = -1
    # 有格栅
    if check_has_steel(refine_result):
        event_id4 = Event.hasSteel
        event_id5 = Event.noSteel_aboveThresh_noPerson
    # 无格栅
    else:
        event_id4 = Event.noSteel
        if get_event_duration(context, 4, Event.noSteel) < event_timeout[Event.noSteel]:
            event_id5 = Event.noSteel_aboveThresh_noPerson
        else:
            if check_has_person(refine_result):
                event_id5 = Event.noSteel_aboveThresh_hasPerson
            else:
                event_id5 = Event.noSteel_aboveThresh_noPerson
    update_event_duration(context, 4, event_id4)
    update_event_duration(context, 5, event_id5)

    if get_event_duration(context, 1, Event.hasHole) > event_timeout[Event.hasHole]:
        alarm_event_id.append(19)
    if get_event_duration(context, 3, Event.noCar_aboveThresh_hasPerson) > event_timeout[Event.noCar_aboveThresh_hasPerson]:
        alarm_event_id.append(20)
    if get_event_duration(context, 5, Event.noSteel_aboveThresh_hasPerson) > event_timeout[Event.noCar_aboveThresh_hasPerson]:
        alarm_event_id.append(21)
    
    # print("event_id:", event_id1, event_id2, event_id3)
    # print("event_duration:", get_event_duration(context, 1, Event.hasHole), get_event_duration(context, 3, Event.noCar_aboveThresh_hasPerson))
    # print("alarm_event_id:", alarm_event_id)


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
        if id == 20:
            display_info.append("未架设钢格栅(无车)")
        if id == 21:
            display_info.append("未架设钢格栅(长时间作业)")
    
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
                        post_time - context['post_alarm_event_id'][id] > properties.post_time_interval['tunnel']:
                context['post_alarm_event_id'][id] = post_time
                need_post = True
    
    if need_post:
        ret["need_post"] = True
        ret['post_time'] = post_time

        logger.info(display_info)
        context['post_time'] = post_time
        # context['post_alarm_event_id'] = alarm_event_id

        alarm_image = tunnel_plot(pred_result.orig_img, ret)
        cv2.imwrite(f"{properties.alarm_image_save_path}/tunnel-{post_time}.jpg", alarm_image)
        cv2.imwrite(f"{properties.alarm_image_save_path}/tunnel-{post_time}_orig.jpg", pred_result.orig_img)

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
        camera_alarm_data["md5Check"] = utils.net.generate_md5_checksum(camera_alarm_data["equipmentId"] 
                                                                   + camera_alarm_data["time"] 
                                                                   + camera_alarm_data["alarmType"] + properties.md5_salt)
        post_data["data"].append(camera_alarm_data)
        
        logger.info(f'📨 {post_data}')

        camera_alarm_data["alarmImage"] = utils.imgproc.image_to_base64(alarm_image, resize_f=1.)
        utils.net.post(properties.post_addr, post_data, logger=logger)

    return ret


def tunnel_plot(img, alarm_result, **kwargs):
    img_ret = deepcopy(img)
    # 画边界框
    if 'polygon' in alarm_result:
        img_ret = cv2.polylines(img_ret, [alarm_result['polygon'].astype(np.int32)], isClosed=True, color=(255,0,0), thickness=3)
    # 画目标框
    if 'refine_result' in alarm_result:
        img_ret = alarm_result['refine_result'].plot(img=img_ret, conf=True)
        # boxes = alarm_result['refine_result'].boxes.xyxy.cpu().numpy().astype(np.int32)
    # 画警报信息
    if 'display_info' in alarm_result:
        img_ret = draw_text(img_ret, alarm_result['display_info'])
    return img_ret
