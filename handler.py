import os
os.environ['YOLO_VERBOSE'] = 'False'    # Don't adjust the position of this code

import sys
import cv2
import copy
import threading
import time
import queue
import gc
import numpy as np
import multiprocessing as mp
import logging
import random
import traceback
from ultralytics import YOLO
from ultralytics.engine.results import Results
from memory_profiler import memory_usage

sys.path.append(".")
import utils
import config

from utils.imgproc import BufferlessVideoCapture, draw_text
from utils.monitor import FpsMonitor
from utils.playback import PlaybackHandler
from utils.stream import StreamPusher

def video_alarm_handler(video_addr:str, model, interval:float=1., 
                        alarm_func=None, plot_func=None, 
                        display:bool=False, save:bool=False, push_stream:bool=False, playback:bool=False,
                        response_queue:mp.Queue=None, **kwargs):
    # config
    stream = kwargs['stream'] if 'stream' in kwargs else False      # to use stream video reader
    context = kwargs['context'] if 'context' in kwargs else {}      # to store task context data
    monitor = kwargs['monitor'] if 'monitor' in kwargs else False
    # model setting
    device = kwargs['device'] if 'device' in kwargs else 'cuda:0'
    infer_imgsz = kwargs['imgsz'] if 'imgsz' in kwargs else 640

    # create logger
    log_file = None
    context['logger_name'] = 'BaseLogger'
    logger = logging.getLogger(context['logger_name'])
    logger.setLevel(level = logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(processName)s - %(message)s')
    # console output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    # file output
    if 'log' in kwargs or 'log_file' in kwargs:
        log_file = kwargs['log_file'] if 'log_file' in kwargs else \
            f'logs/{mp.current_process().name}_' + time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime()) + '.txt'
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f'save logs to: {log_file}')


    # extra setting
    if not os.path.isfile(video_addr) and not stream:
        stream = True
        logger.warning('🟡 Found input is not a file, set stream=True')

    # 载入模型
    if not isinstance(model, YOLO):
        model = YOLO(model)
    # model.predict('resources/bus.jpg')

    # 载入视频
    capture = cv2.VideoCapture(video_addr)
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    # capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

    fps = int(capture.get(cv2.CAP_PROP_FPS))
    shape = (int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    frame_num = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    logger.info('source:\t' + str(video_addr))
    logger.info('shape:\t' + str(shape))
    logger.info('fps:\t' + str(fps))
    logger.info('frame:\t' + str(frame_num))
    if shape[0] == 0 or shape[1] == 0:
        logger.warning(f'🛑 Cannot get video {video_addr}, about to exit')

    if stream:
        capture = BufferlessVideoCapture(capture, logger=logger)

    # 创建视频显示
    if display:
        if 'display_shape' not in kwargs:
            kwargs['display_shape'] = 1.
        display_shape = (int(shape[0] * kwargs['display_shape']), int(shape[1] * kwargs['display_shape']))
        window_name = "Inference: " + str(video_addr)

    # 创建视频文件
    if save:
        if 'save_path' not in kwargs:
            kwargs['save_path'] = './runs/' + time.strftime('%Y-%m-%d %H_%M_%S', time.localtime()) + '.mp4'
        if 'save_shape' not in kwargs:
            kwargs['save_shape'] = 1.
        save_shape = (int(shape[0] * kwargs['save_shape']), int(shape[1] * kwargs['save_shape']))
        writer = cv2.VideoWriter(kwargs['save_path'], cv2.VideoWriter_fourcc(*'mp4v'), fps, save_shape)
        logger.info("save video to: " + kwargs['save_path'])

    # 创建视频推流
    if push_stream:
        if 'push_shape' not in kwargs: kwargs['push_shape'] = 1.
        push_shape = [int(shape[0] * kwargs['push_shape']), int(shape[1] * kwargs['push_shape'])]
        for i in range(len(push_shape)):    # 令视频高宽变为偶数
            if push_shape[i] % 2 == 1: push_shape[i] += 1
        stream_pusher = StreamPusher(url=kwargs['push_url'], shape=push_shape, fps=fps)

    # 创建回放处理
    if playback:
        playback_resize_f = 0.5
        playback_shape = (int(shape[0] * playback_resize_f), int(shape[1] * playback_resize_f))
        playback_buff = mp.Queue(fps)
        playback_proc = mp.Process(target=PlaybackHandler.playbcak_proc_task, daemon=True,
                                    kwargs={'in_conn': playback_buff, 'shape': playback_shape, 'fps': fps ,
                                            'trace_time': 60., 'log_file': log_file })
        playback_proc.start()
        context['playback_warn_time'] = 0
    
    # FPS
    if monitor:
        monitor = FpsMonitor(window_size=60, flash_interval=2.)
    
    # 初始化计时
    context['prev_detect_time'] = 0
    context['prev_gc_time'] = 0
    context['prev_used_time'] = 0

    enable_plot = (display or save or push_stream or playback)
    frame_cnt = 0
    laplacian_fuzzy = False
    used_times = []
    retry_cnt, max_retry, prev_retry_time = 0, 3, 0

    logger.info(f'🔧 User Args: {kwargs}')
    logger.info(f'🟢 Start process: {mp.current_process().name}')

    # 主循环
    while True:
        try:
            curr_loop_time = time.time()
            used_times.append(('start', curr_loop_time))

            ret, frame = capture.read()
            if not ret:
                if 'loop' in kwargs and kwargs['loop']:     # loop video
                    capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    break
            used_times.append(('cam', time.time()))

            # 目标检测
            if curr_loop_time - context['prev_detect_time'] > interval:
                laplacian_fuzzy = False
                # laplacian_fuzzy = utils.imgproc.variance_of_laplacian(cv2.resize(frame, (0,0), fx=0.3, fy=0.3))
                # laplacian_fuzzy = laplacian_fuzzy < config.laplacian_threshold
                # if laplacian_fuzzy:
                #     logger.info('laplacian fuzzy')
                
                if not laplacian_fuzzy:
                    context['prev_detect_time'] = curr_loop_time
                    pred_result = model(frame, device=device, imgsz=infer_imgsz)[0]
                    used_times.append(('yolo', time.time()))
                    if alarm_func is not None:
                        # 报警信息
                        alarm_result = alarm_func(pred_result, context=context)
                        used_times.append(('alarm', time.time()))

            # plot到当前帧
            if enable_plot:
                if laplacian_fuzzy:
                    annotated_frame = draw_text(frame, [f"{context['post_data']['name'].split('-')[-1]}路", "当前图像模糊"])
                else:
                    if plot_func is not None:
                        annotated_frame = plot_func(frame, alarm_result=alarm_result, context=context)
                    else:
                        annotated_frame = pred_result.plot(img=frame)
                used_times.append(('plot', time.time()))
            
            # 显示视频
            if display:
                display_frame = cv2.resize(annotated_frame, display_shape)
                cv2.imshow(window_name, display_frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                used_times.append(('display', time.time()))

            # 保存视频
            if save:
                write_frame = cv2.resize(annotated_frame, save_shape)
                writer.write(write_frame)
                used_times.append(('save', time.time()))

            # 回放
            if playback:
                try:
                    playback_buff.put((0, annotated_frame), block=False)
                    if alarm_result['need_post']:
                        playback_buff.put((1, alarm_result['post_time']), block=False)
                        alarm_result['need_post'] = False
                except queue.Full:
                    if curr_loop_time - context['playback_warn_time'] > 60.:
                        context['playback_warn_time'] = curr_loop_time
                        logger.warning(f'🟡 Playback_buff full {frame_cnt}')
                    pass
                used_times.append(('playback', time.time()))

            # 推视频流
            if push_stream:
                push_frame = cv2.resize(annotated_frame, push_shape)
                stream_pusher.push(push_frame)
                used_times.append(('push', time.time()))

            # gc
            if curr_loop_time - context['prev_gc_time'] > config.gc_interval:
                context['prev_gc_time'] = curr_loop_time
                gc.collect()
                logger.debug(f"🗑️ Garbage collected, current memory: {str(memory_usage(-1, interval=.1, timeout=.1)[0])}MB")

            # fps
            if monitor:
                monitor.count += 1
                monitor.flash()

            if response_queue is not None:
                response_queue.put({'pid': mp.current_process().pid, 
                                    'timestamp': time.time(), 
                                    'code': 0, 'msg': 'ok', })

            frame_cnt = (frame_cnt + 1) % config.MAXINT

            # used-time statistics
            if curr_loop_time == context['prev_detect_time'] and curr_loop_time - context['prev_used_time'] > config.used_time_stats_interval:
                used_time_info = f'total={used_times[-1][1] - used_times[0][1]:.3f} '
                for i in range(1, len(used_times)):
                    used_time_info += f'{used_times[i][0]}={used_times[i][1] - used_times[i-1][1]:.3f} '
                logger.debug(f'Time statistics {frame_cnt}:, {used_time_info}')
                context['prev_used_time'] = curr_loop_time
            used_times.clear()

        except KeyboardInterrupt:
            break
        except Exception:
            curr_time = time.time()
            if curr_time - prev_retry_time > 60 * 60 and retry_cnt > 0:
                retry_cnt -= 1
                logger.debug('⭕ Recovered from previous exception')
            
            logger.error(traceback.format_exc())
            retry_cnt += 1
            prev_retry_time = curr_time
            
            if retry_cnt > max_retry:
                logger.error('⭕ Occurred too many exceptions, exit')
                break

            logger.error(f'⭕ Retrying: {retry_cnt} / {max_retry}')


    # 释放资源
    capture.release()
    if display:
        cv2.destroyAllWindows()
    if save:
        writer.release()
    if push_stream:
        stream_pusher.close()
    if playback:
        playback_proc.terminate()
    if monitor:
        monitor.close()

    logger.info(f'🛑 End Process: {mp.current_process().name}')



def keep_proc_alive(response_queue:mp.Queue, proc_status:dict, logger:logging.Logger):
    """
    A function to keep a list of processes alive by monitoring response queue and process status.
    
    Parameters:
    - response_queue: a multiprocessing Queue for receiving responses
        format:
            {'pid': Process.pid, 
            'timestamp': time.time(), 
            'code': 0, 'msg': 'ok', }
    - proc_status: a dictionary containing information about running processes
        format:
            key: Process.pid
            value: {'object': Process, 'kwargs': kwargs, 'timestamp': time.time(), 'code': int, 'msg': str}
    - logger: an instance of logging.Logger
    
    No return value, runs indefinitely until interrupted
    """
    logger.info(f'📛 Keep-process-alive service is running')
    logger.info(f'📛 Total {len(proc_status)} processes are running')
    while True:
        try:    # get response
            response = response_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            rcd = proc_status[response['pid']]
            rcd['timestamp'] = response['timestamp']
            rcd['code'] = response['code']
            rcd['msg'] = response['msg']

        try:
            new_process_status = {}
            del_process = []
            for pid, rcd in proc_status.items():
                process = rcd['object']
                need_restart = False
                if not process.is_alive():
                    logger.info(f'📛 {process} is dead')
                    need_restart = True
                elif time.time() - rcd['timestamp'] > config.proc_response_timeout:
                    logger.info(f'📛 {process} response timeout')
                    need_restart = True
                if need_restart:    # restart a new process with the same args
                    process.terminate()
                    del_process.append(pid)
                    kwargs = rcd['kwargs']
                    new_proc = mp.Process(target=video_alarm_handler, kwargs=kwargs)
                    new_proc.start()
                    new_process_status[new_proc.pid] = {'object': new_proc, 'kwargs': kwargs, 'timestamp': time.time(), 'code': None, 'msg': ''}
                    logger.info(f'📛 Restart {new_proc} to alternate {process.name}')

            for pid in del_process:
                del proc_status[pid]
            proc_status.update(new_process_status)

        except KeyboardInterrupt:
            break
        except Exception:
            logger.error(f'📛 MainProcess met error')
            logger.error(traceback.format_exc())


