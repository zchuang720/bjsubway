import os
import sys
import cv2
import copy
import threading
import time
import numpy as np
import multiprocessing
from ultralytics import YOLO

sys.path.append(".")
import utils.net as net
import handler
import properties
import test
from internal.fire.alarm import fire_alarm, fire_plot
from internal.grid.alarm import grid_alarm, grid_plot
from internal.pipe.alarm import pipe_alarm, pipe_plot


def main():
    pipe_num = 4
    fire_num = 4
    grid_num = 4
    for i in range(pipe_num):
        process = multiprocessing.Process(target=handler.video_alarm_handler, name=f'pipe{i+1}', kwargs={
                                'video_addr': properties.pipe_cam_addr_stress[i], 'model': 'weights/pipe_m.pt', 
                                'alarm_func': pipe_alarm, 'plot_func': pipe_plot, 'interval': 0.5, 
                                'display': False, 'display_shape': 0.3, 'save': False, 'save_shape': 0.5, 
                                'push_stream': True, 'push_url': properties.pipe_push_url_stress[i], 'push_shape':0.4, 
                                'loop': True, 'sync': False, 'debug': True})
        process.start()
    for i in range(fire_num):
        process = multiprocessing.Process(target=handler.video_alarm_handler, name=f'fire{i+1}', kwargs={
                                'video_addr': 'resources/fire_1.avi', 'model': 'weights/fire_m.pt', 
                                'alarm_func': fire_alarm, 'plot_func': fire_plot, 'interval': 0.2, 
                                'display': False, 'display_shape': 0.3, 'save': False, 'save_shape': 0.5, 
                                'push_stream': True, 'push_url': properties.fire_push_url_stress[i], 'push_shape':0.4, 
                                'loop': True, 'sync': False, 'debug': True})
        process.start()
    for i in range(grid_num):
        process = multiprocessing.Process(target=handler.video_alarm_handler, name=f'grid{i+1}', kwargs={
                                'video_addr': 'resources/grid_1.mp4', 'model': 'weights/tunnel_grid_v8s.pt', 
                                'alarm_func': grid_alarm, 'plot_func': grid_plot, 'interval': 1., 
                                'display': False, 'display_shape': 0.3, 'save': False, 'save_shape': 0.5, 
                                'push_stream': True, 'push_url': properties.grid_push_url_stress[i], 'push_shape':0.5, 
                                'loop': True, 'sync': False, 'debug': True})
        process.start()


if __name__ == "__main__":
    test.test_demo_Dec_12()