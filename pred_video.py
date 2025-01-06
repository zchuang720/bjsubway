import sys
sys.path.append("..")
import multiprocessing as mp
import handler
from internal.fire.alarm import fire_alarm, fire_plot
from internal.grid.alarm import grid_alarm, grid_plot
from internal.pipe_ground.alarm import pipe_alarm, pipe_plot
from internal.tunnel.alarm import tunnel_alarm, tunnel_plot

def pred_video():
    context = {'post_data': {'name': '', 'equipmentId': '', }}
    handler.video_alarm_handler(video_addr=r'resources/fire_trim_20min.mp4',
                                model=r'weights/yanshou_donghuo.pt',
                                alarm_func=fire_alarm, plot_func=fire_plot,
                                interval=0.2, display=False, display_shape=0.5,
                                save=False, loop=False, imgsz=1280,
                                context=context)


def mp_test():
    for i in range(10):
        mp.Process(target=pred_video).start()

if __name__ == '__main__':
    pred_video()