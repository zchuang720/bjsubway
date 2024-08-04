import sys
sys.path.append("..")
import multiprocessing as mp
import handler
from models.fire.alarm import fire_alarm, fire_plot
from models.grid.alarm import grid_alarm, grid_plot
from models.pipe_ground.alarm import pipe_alarm, pipe_plot
from models.tunnel.alarm import tunnel_alarm, tunnel_plot
import multiprocessing

def pred_video():
    context = {'post_data': {'name': '', 'equipmentId': '', }}
    handler.video_alarm_handler(video_addr=r'resources\tunnel01.mp4',
                                model=r'weights\tunne-carl-l-seg-best.pt',
                                alarm_func=tunnel_alarm, plot_func=tunnel_plot,
                                interval=0.5, display=True, display_shape=0.5,
                                save=False, loop=False, imgsz=640,
                                monitor=True, context=context)


def mp_test():
    for i in range(10):
        mp.Process(target=pred_video).start()

if __name__ == '__main__':
    pred_video()