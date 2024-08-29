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
    handler.video_alarm_handler(video_addr=r'resources/tunnel-0824.mp4',
                                model=r'weights/tunnel-seg-l-1280-0828.pt',
                                alarm_func=tunnel_alarm, plot_func=tunnel_plot,
                                interval=0.1, display=True, display_shape=0.5,
                                save=False, loop=False, imgsz=1280,
                                context=context)


def mp_test():
    for i in range(10):
        mp.Process(target=pred_video).start()

if __name__ == '__main__':
    pred_video()