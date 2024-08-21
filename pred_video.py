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
    handler.video_alarm_handler(video_addr=r'resources/new_fire_underground.mp4',
                                model=r'weights/fire_size1280_0719.pt',
                                alarm_func=fire_alarm, plot_func=fire_plot,
                                interval=0.2, display=True, display_shape=0.5,
                                save=True, loop=False, imgsz=1280,
                                context=context)


def mp_test():
    for i in range(10):
        mp.Process(target=pred_video).start()

if __name__ == '__main__':
    pred_video()