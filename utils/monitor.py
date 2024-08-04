from collections import deque
import multiprocessing
import time
from matplotlib import pyplot as plt


class FpsMonitor:
    def __init__(self, window_size=60, flash_interval=2.):
        self.window_size = window_size  # seconds
        self.flash_interval = flash_interval

        # 初始化Matplotlib图形
        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.fig.canvas.manager.set_window_title(f'FPS Monitor - {multiprocessing.current_process().name}')
        self.x_data = deque(maxlen=self.window_size)
        self.y_data = deque(maxlen=self.window_size)
        self.line, = self.ax.plot(self.x_data, self.y_data, label='FPS')
        self.ax.get_xaxis().set_visible(False)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        
        self.count = 0
        self.start_time = time.time()

    def flash(self):
        curr_time = time.time()
        elapsed_time = curr_time - self.start_time

        if elapsed_time > self.flash_interval:
            fps = self.count / elapsed_time

            self.count = 0
            self.start_time = curr_time

            # 更新Matplotlib图形
            self.x_data.append(curr_time)
            self.y_data.append(fps)
            self.line.set_xdata(self.x_data)
            self.line.set_ydata(self.y_data)
            self.ax.relim()
            self.ax.autoscale_view()
            # plt.text(curr_time, fps, f"{fps:.0f}", fontdict={'size':'10','color':'b'})

            # 更新图形显示
            plt.draw()
            plt.pause(0.0001)

            # print(f'⏱️ FPS: {fps:.2f}')

    def close(self):
        plt.ioff()
        # plt.show()
        plt.close()
