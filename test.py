import os
os.environ['YOLO_VERBOSE'] = 'False'
import sys
import cv2
import copy
import re
import threading
import time
import logging
import traceback
import numpy as np
import queue
import multiprocessing
from threading import Thread
from ultralytics import YOLO
from ultralytics.engine.results import Boxes, Results

sys.path.append(".")
import utils.net as net
import properties
import config
from models.fire.alarm import fire_alarm, fire_plot
from models.grid.alarm import grid_alarm, grid_plot
from models.pipe_ground.alarm import pipe_alarm, pipe_plot
import handler


def test_post():
    post_data = copy.deepcopy(properties.post_data_dict)
    post_data["equipment_type"] = "camera"
    post_data["event_type"] = "alarm"

    camera_alarm_data = copy.deepcopy(properties.camera_alarm_data_dict)
    camera_alarm_data["model"] = "2"
    camera_alarm_data["brand"] = "brand"
    camera_alarm_data["equipmentId"] = "equipmentId"
    camera_alarm_data["alarmType"] = "4"
    camera_alarm_data["alarmImage"] = ""
    camera_alarm_data["alarmUrl"] = ""
    camera_alarm_data["name"] = "name"
    camera_alarm_data["time"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    camera_alarm_data["gongdiSN"] = properties.gongdiSN
    camera_alarm_data["latitude"] = ""
    camera_alarm_data["longitude"] = ""
    camera_alarm_data["alarmInfo"] = ""
    camera_alarm_data["md5Check"] = net.generate_md5_checksum(
                                        camera_alarm_data["brand"] + camera_alarm_data["equipmentId"] \
                                        + properties.md5_salt)
    post_data["data"].append(camera_alarm_data)
    print(post_data)
    
    net.post(properties.post_addr, post_data)


def test_video_stream(video_addr):
    """
    Opens a video stream from the given video address and displays it in a window.
    
    Parameters:
        video_addr (str): The address or path of the video file.
        
    Returns:
        None
    """
    capture = cv2.VideoCapture(video_addr)

    fps = int(capture.get(cv2.CAP_PROP_FPS))
    shape = (int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    frame_num = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    print('source:\t' + str(video_addr))
    print('shape:\t' + str(shape))
    print('fps:\t' + str(fps))
    print('frame:\t' + str(frame_num))

    while True:
        ret, frame = capture.read()
        if not ret:
            break
        cv2.imshow("Video", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    capture.release()
    cv2.destroyAllWindows()


def test_yolo(video_addr=None, weight_path=None, interval=1, alarm_func=None, display=True):
    """
    This function is used to test the YOLO object detection algorithm on a video.

    Args:
        video_addr (str, optional): The address/path of the video file to be used for object detection. Defaults to None.
        weight_path (str, optional): The address/path of the weight file for the YOLO model. Defaults to None.
        interval (int, optional): The interval between frames for object detection. Defaults to 1.
        alarm_func (function, optional): The callback function to be called when an object is detected. Defaults to None.
        display (bool, optional): Whether to display the video with object annotations. Defaults to True.

    Returns:
        None
    """
    if weight_path is None:
        weight_path = "weights/yolov8n.pt"
    model = YOLO(weight_path)
    
    if video_addr is None:
        video_addr = "resources/car.mp4"
    capture = cv2.VideoCapture(video_addr)

    fps = int(capture.get(cv2.CAP_PROP_FPS))
    shape = (int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    frame_num = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print('source:\t' + str(video_addr))
    print('shape:\t' + str(shape))
    print('fps:\t' + str(fps))
    print('frame:\t' + str(frame_num))

    interval = int(fps * interval)
    frame_cnt = 0

    while capture.isOpened():
        ret, frame = capture.read()
        if not ret:
            break

        is_detect = (frame_cnt % interval == 0)
        if is_detect:
            pred_result = model(frame)[0]
            if alarm_func is not None:
                alarm_func(pred_result)

        if display:
            pred_result.orig_img = frame
            annotated_frame = pred_result.plot()
            annotated_frame = cv2.resize(annotated_frame, (int(shape[0]*0.5), int(shape[1]*0.5)))
            cv2.imshow("Inference", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        frame_cnt += 1

    capture.release()
    if display:
        cv2.destroyAllWindows()


def test_main():
    # handler.video_alarm_handler(video_addr='resources/pipe_3.dav', model='weights/pipe_m_v3.pt', 
    #                             alarm_func=pipe_alarm, plot_func=pipe_plot, 
    #                             interval=0.5, display=True, display_shape=0.5, save=False, save_shape=1.,
    #                             push_stream=False, push_url=data.pipe_push_url[0], push_shape=0.5, 
    #                             loop=True)
    cam_name = '安全管理-新龙泽站-主体-可见光检测-001'
    cam_ip = re.search(r'rtsp://\w+:\w+@([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', properties.gongdi04_cam_addr[cam_name]).group(1)
    push_addr = 'rtsp://localhost/fire/' + cam_ip
    context = {'post_data': {'name': cam_name, 'equipmentId': cam_name, }}
    # handler.video_alarm_handler(video_addr=data.gongdi04_cam_addr[cam_name], model='weights/fire_m_v5.pt', 
    #                             alarm_func=fire_alarm, plot_func=fire_plot,
    #                             interval=0.2, display=True, display_shape=0.3,
    #                             push_stream=True, push_url=push_addr, push_shape=0.5, 
    #                             loop=True, stream=False, playback=False, monitor=False, 
    #                             context=context)
    handler.video_alarm_handler(video_addr=properties.gongdi04_cam_addr[cam_name], model='weights/pipe_m_v4.pt', 
                                alarm_func=pipe_alarm, plot_func=pipe_plot,
                                interval=1., display=True, display_shape=0.5,
                                push_stream=True, push_url=push_addr, push_shape=0.5, 
                                loop=True, stream=False, playback=False, monitor=False, 
                                context=context)
    

def test_stress():
    pipe_num = 1
    fire_num = 1
    grid_num = 1
    playback = True
    push_stream = True
    for i in range(pipe_num):
        process = multiprocessing.Process(target=handler.video_alarm_handler, name=f'pipe-{i+1}', kwargs={
                                'video_addr': 'resources/pipe_1.dav', 'model': 'weights/pipe_m_v3.pt', 
                                'alarm_func': pipe_alarm, 'plot_func': pipe_plot, 'interval': 0.5, 
                                'display': True, 'display_shape': 0.3, 
                                'push_stream': push_stream, 'push_url': properties.pipe_push_url_stress[i], 'push_shape':0.4, 
                                'loop': True, 'stream': False, 'monitor': True, 'playback': playback})
        process.start()
    for i in range(fire_num):
        process = multiprocessing.Process(target=handler.video_alarm_handler, name=f'fire-{i+1}', kwargs={
                                'video_addr': 'resources/fire_2.avi', 'model': 'weights/fire_m_v4.pt', 
                                'alarm_func': fire_alarm, 'plot_func': fire_plot, 'interval': 0.2, 
                                'display': True, 'display_shape': 0.3,
                                'push_stream': push_stream, 'push_url': properties.fire_push_url_stress[i], 'push_shape':0.4, 
                                'loop': True, 'stream': False, 'monitor': True, 'playback': playback})
        process.start()
    for i in range(grid_num):
        process = multiprocessing.Process(target=handler.video_alarm_handler, name=f'grid-{i+1}', kwargs={
                                'video_addr': 'resources/grid_1.mp4', 'model': 'weights/tunnel_grid_v8s.pt', 
                                'alarm_func': grid_alarm, 'plot_func': grid_plot, 'interval': 1., 
                                'display': True, 'display_shape': 0.3, 
                                'push_stream': push_stream, 'push_url': properties.grid_push_url_stress[i], 'push_shape':0.5, 
                                'loop': True, 'stream': False, 'monitor': True, 'playback': playback})
        process.start()


def test_playback():
    handler.video_alarm_handler(video_addr='resources/pipe_1.dav', model='weights/pipe_m.pt', 
                                alarm_func=pipe_alarm, plot_func=pipe_plot, imgsz=640,
                                interval=0.5, display=False, display_shape=0.3, save=False, save_shape=1.,
                                playback=False, loop=False, debug=False)

def test_demo_Dec_12():
    fire_process = multiprocessing.Process(target=handler.video_alarm_handler, name=f'fire-动火01', kwargs={
                            'video_addr': properties.pipe_cam_addr[0], 'model': 'weights/fire_m_v4.pt', 
                            'alarm_func': fire_alarm, 'plot_func': fire_plot, 'interval': 0.05, 
                            'display': True, 'display_shape': 0.4, 'save': False, 'save_shape': 0.5, 
                            'push_stream': True, 'push_url': properties.fire_push_url_stress[0], 'push_shape':0.6, 
                            'loop': True, 'sync': False, 'log': True, 'stream': True})
    fire_process.start()
    pipe_process = multiprocessing.Process(target=handler.video_alarm_handler, name=f'pipe-钢支撑01', kwargs={
                            'video_addr': properties.pipe_cam_addr[1], 'model': 'weights/pipe_m_v3.pt', 
                            'alarm_func': pipe_alarm, 'plot_func': pipe_plot, 'interval': 0.2, 
                            'display': True, 'display_shape': 0.4, 'save': False, 'save_shape': 0.5, 
                            'push_stream': True, 'push_url': properties.pipe_push_url_stress[0], 'push_shape':0.6, 
                            'loop': True, 'sync': False, 'log': True, 'stream': True})
    pipe_process.start()
    pipe_process = multiprocessing.Process(target=handler.video_alarm_handler, name=f'pipe-钢支撑02', kwargs={
                            'video_addr': properties.pipe_cam_addr[0], 'model': 'weights/pipe_m_v3.pt', 
                            'alarm_func': pipe_alarm, 'plot_func': pipe_plot, 'interval': 0.2, 
                            'display': True, 'display_shape': 0.4, 'save': False, 'save_shape': 0.5, 
                            'push_stream': True, 'push_url': properties.pipe_push_url_stress[1], 'push_shape':0.6, 
                            'loop': True, 'sync': False, 'log': True, 'stream': True})
    pipe_process.start()


def test_gongdi04_24_3_10():
    log_file = 'logs/' + time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime()) + '.txt'
    logger = logging.getLogger('MainLogger')
    logger.setLevel(level = logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(processName)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    response_queue = multiprocessing.Queue()
    proc_status = {}
    
    enable_push_stream = True
    enable_playback = False
    # fire
    cam_names = ['新龙泽站-主体基坑西区-南墙-004', '新龙泽站-主体基坑西区-南墙-008', '新龙泽站-主体基坑西区-北墙-012',
                 '安全管理-新龙泽站-轨道公司演示002', '安全管理-新龙泽站-主体-可见光检测-001']
    for cam_name in cam_names:
        cam_addr = properties.gongdi04_cam_addr[cam_name]
        cam_ip = re.search(r'rtsp://\w+:\w+@([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', cam_addr).group(1)
        push_addr = 'rtsp://localhost/fire/' + cam_ip
        context = {'post_data': {'name': cam_name, 'equipmentId': f'fire-{cam_ip}', 'brand': '久译'}}
        alarm_func = [fire_alarm, fire_plot]
        # alarm_func = [fire_2.fire_alarm, fire_2.fire_plot] if '基坑' in cam_name else [fire_alarm, fire_plot]
        kwargs = {'video_addr': cam_addr, 'model': 'weights/fire_m_v5.pt', 
                    'alarm_func': alarm_func[0], 'plot_func': alarm_func[1], 'interval': 0.2, 
                    'display': True, 'display_shape': 0.3, 'infer_imgsz': 1280,
                    'push_stream': enable_push_stream, 'push_url': push_addr, 'push_shape':0.6, 
                    'loop': True, 'stream': False, 'monitor': False, 'playback': enable_playback, 
                    'context': context, 'log_file': log_file, 'response_queue': response_queue}
        process = multiprocessing.Process(target=handler.video_alarm_handler, kwargs=kwargs)
        process.start()
        proc_status[process.pid] = {'object': process, 'kwargs': kwargs, 'timestamp': time.time(), 'code': None, 'msg': ''}
    # pipe
    cam_names = ['新龙泽站-主体基坑西区-南墙-009', '新龙泽站-主体基坑西区-南墙-008',
                 '新龙泽站-主体基坑西区-北墙-012', '新龙泽站-主体基坑西区-北墙-014']
    for cam_name in cam_names:
        cam_addr = properties.gongdi04_cam_addr[cam_name]
        cam_ip = re.search(r'rtsp://\w+:\w+@([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', cam_addr).group(1)
        push_addr = 'rtsp://localhost/pipe/' + cam_ip
        context = {'post_data': {'name': cam_name, 'equipmentId': f'pipe-{cam_ip}', 'brand': '久译'}}
        kwargs = {'video_addr': cam_addr, 'model': 'weights/pipe_m_v4.pt', 
                    'alarm_func': pipe_alarm, 'plot_func': pipe_plot, 'interval': 2., 
                    'display': True, 'display_shape': 0.3,
                    'push_stream': enable_push_stream, 'push_url': push_addr, 'push_shape':0.6, 
                    'loop': True, 'stream': False, 'monitor': False, 'playback': enable_playback, 
                    'context': context, 'log_file': log_file, 'response_queue': response_queue}
        process = multiprocessing.Process(target=handler.video_alarm_handler, kwargs=kwargs)
        process.start()
        proc_status[process.pid] = {'object': process, 'kwargs': kwargs, 'timestamp': time.time(), 'code': None, 'msg': ''}

    # handler.keep_proc_alive(response_queue, proc_status, logger)


def test_gongdi03_24_4_22():
    log_file = 'logs/' + time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime()) + '.txt'
    logger = logging.getLogger('MainLogger')
    logger.setLevel(level = logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(processName)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    response_queue = multiprocessing.Queue()
    proc_status = {}
    
    enable_push_stream = True
    enable_playback = False
    # tunnel
    cam_names = ['B-021']
    for cam_name in cam_names:
        cam_addr = properties.gongdi03_cam_addr[cam_name]
        cam_ip = re.search(r'rtsp://\w+:\w+@([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', cam_addr).group(1)
        push_addr = 'rtsp://localhost:556/tunnel/' + cam_ip
        context = {'post_data': {'name': cam_name, 'equipmentId': f'tunnel-{cam_ip}', 'brand': '久译'}}
        alarm_func = [grid_alarm, grid_plot]
        kwargs = {'video_addr': cam_addr, 'model': 'weights/tunne-carl-l-seg-best.pt', 
                    'alarm_func': alarm_func[0], 'plot_func': alarm_func[1], 'interval': 1., 
                    'display': True, 'display_shape': 0.6, 'infer_imgsz': 1280,
                    'push_stream': enable_push_stream, 'push_url': push_addr, 'push_shape':0.6, 
                    'loop': True, 'stream': True, 'monitor': False, 'playback': enable_playback, 
                    'context': context, 'log_file': log_file, 'response_queue': response_queue}
        process = multiprocessing.Process(target=handler.video_alarm_handler, kwargs=kwargs)
        process.start()
        proc_status[process.pid] = {'object': process, 'kwargs': kwargs, 'timestamp': time.time(), 'code': None, 'msg': ''}

    # handler.keep_proc_alive(response_queue, proc_status, logger)



if __name__ == "__main__":
    test_gongdi03_24_4_22()
