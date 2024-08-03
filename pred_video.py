import multiprocessing as mp
import handler2
import handler
from models.fire.alarm import fire_alarm, fire_plot
from models.grid.alarm import grid_alarm, grid_plot
from models.pipe_ground.alarm import pipe_alarm, pipe_plot
import multiprocessing
# def pred_video():
#     context = {'post_data': {'name': '', 'equipmentId': '', }}
#     handler2.video_alarm_handler(video_addr=r'/home/user/bjtu/bjsubway/resources/new_pipe_raw.mp4',
#                                 model=r'/home/user/bjtu/bjsubway/weights/pipe_ground_seg_l_v1_size1280.pt',
#                                 alarm_func=pipe_alarm, plot_func=pipe_plot,
#                                 interval=0., display=True, display_shape=0.5,
#                                 save=True, loop=False,imgsz=1920,
#                                 context=context,fps_stride=25)

def pred_video():
    context = {'post_data': {'name': '', 'equipmentId': '', }}
    handler.video_alarm_handler(video_addr=r'/home/user/bjtu/bjsubway/resources/new_fire_underground.mp4',
                                model=r'/home/user/bjtu/bjsubway/weights/fire_size1280_0719.pt',
                                alarm_func=fire_alarm, plot_func=fire_plot,
                                interval=0., display=True, display_shape=0.5,
                                save=True, loop=False,imgsz=1920,
                                context=context)


def mp_test():
    for i in range(10):
        mp.Process(target=pred_video).start()

if __name__ == '__main__':
    pred_video()