import subprocess


class StreamPusher:
    def __init__(self, url, shape, fps):
        if fps <= 1:
            fps = 25
        if shape[0] == 0 or shape[1] == 0:
            shape = (1920, 1080)
        # 创建FFmpeg命令行参数
        ffmpeg_cmd = ['ffmpeg',                 # linux不用指定
                    '-y', '-an',
                    '-f', 'rawvideo',
                    '-vcodec','rawvideo',
                    '-pix_fmt', 'bgr24',        #像素格式
                    '-s', "{}x{}".format(shape[0], shape[1]),
                    # '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2',
                    '-r', str(fps),             # 自己的摄像头的fps是0，若用自己的notebook摄像头，设置为15、20、25都可。 
                    '-i', '-',
                    '-flush_packets', '1',
                    '-c:v', 'libx264',          # 视频编码方式
                    '-pix_fmt', 'yuv420p',
                    '-preset', 'ultrafast',
                    '-f', 'rtsp',               #  flv rtsp
                    '-rtsp_transport', 'udp',   # 使用TCP推流，linux中一定要有这行
                    url]                        # rtsp rtmp  
        # print('ffmpeg_cmd:', ffmpeg_cmd)
        # 启动 ffmpeg
        self.ffmepg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, bufsize=0)

    def push(self, frame):
        self.ffmepg_process.stdin.write(frame.tostring())
        self.ffmepg_process.stdin.flush()
    
    def close(self):
        self.ffmepg_process.kill()
    
