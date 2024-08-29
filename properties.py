# test
# post_addr = 'https://zhgd.beijingmcc.com:99/device/log'
# post_addr = 'https://zhgd.beijingmcc.com:3001/eqlog/log'
# gongdiSN = '191000TE'

# 04
post_addr_04 = 'http://172.17.104.99:8099/device-front/log'
gongdiSN_04 = '13040224'
# 03
# post_addr_03 = 'http://111.198.54.249:6203/device-front/log'
post_addr_03 = 'https://zhgd.beijingmcc.com:3001/eqlog/log'
gongdiSN_03 = '13-03'

# real
post_addr = post_addr_03
gongdiSN = gongdiSN_03

# cam rtsp address
pipe_cam_addr_stress = [f'./resources/stress_test/{i}.mp4' for i in range(1, 25)]
gongdi04_cam_addr = {
    '安全管理-新龙泽站-轨道公司演示002': 'rtsp://admin:admin123@192.168.1.234/cam/realmonitor?channel=1&subtype=0',
    '安全管理-新龙泽站-轨道公司演示003': 'rtsp://admin:admin123@192.168.1.235/cam/realmonitor?channel=1&subtype=0',
    '安全管理-新龙泽站-主体-可见光检测-001': 'rtsp://admin:admin123@192.168.1.213/cam/realmonitor?channel=1&subtype=0',
    # '新龙泽站-主体基坑西区-南墙-007': 'rtsp://admin:yhy12345@192.168.1.221/cam/realmonitor?channel=1&subtype=0',
    '新龙泽站-主体基坑西区-南墙-004': 'rtsp://admin:yhy12345@192.101.4.231/cam/realmonitor?channel=1&subtype=0',
    '新龙泽站-主体基坑西区-南墙-008': 'rtsp://admin:yhy12345@192.101.4.235/cam/realmonitor?channel=1&subtype=0',
    '新龙泽站-主体基坑西区-南墙-009': 'rtsp://admin:yhy12345@192.101.4.234/cam/realmonitor?channel=1&subtype=0',
    '新龙泽站-主体基坑西区-北墙-012': 'rtsp://admin:yhy12345@192.101.4.225/cam/realmonitor?channel=1&subtype=0',
    '新龙泽站-主体基坑西区-北墙-013': 'rtsp://admin:yhy12345@192.101.4.226/cam/realmonitor?channel=1&subtype=0',
    '新龙泽站-主体基坑西区-北墙-014': 'rtsp://admin:yhy12345@192.101.4.228/cam/realmonitor?channel=1&subtype=0',
}

gongdi03_cam_addr = {
    'B-021': 'rtsp://admin:qwe12345@192.101.3.110/cam/realmonitor?channel=1&subtype=0',
    'A-024': 'rtsp://admin:qwe12345@192.101.3.132/cam/realmonitor?channel=1&subtype=0',
}

# push stream address
pipe_push_url = [
    'rtsp://localhost/pipe/video1',
    # 'rtsp://localhost/dss/monitor/param?cameraid=1000085%240&substream=1',
]
fire_push_url = [
    'rtsp://localhost/fire/video1'
]
pipe_push_url_stress = [
    f'rtsp://localhost/pipe/video{i}' for i in range(1, 25)
]
fire_push_url_stress = [
    f'rtsp://localhost/fire/video{i}' for i in range(1, 25)
]
grid_push_url_stress = [
    f'rtsp://localhost/grid/video{i}' for i in range(1, 25)
]

# network services
access_ip_04 = '123.125.19.139'
access_ip_03 = '111.198.54.249'

# playback video url
playback_url = f'http://{access_ip_03}:6101/video'

# post data
md5_salt = 'jtgd2021ZT'

post_data_dict = {
    "equipment_type": "",    # 设备类型,
    "event_type": "",        # 事件类型,
    "data": [],              # [{数据包}, {数据包}, ...]
}

"""
1.	未带安全帽
2.	边界管理报警
3.	动火报警
4.	明挖支护-超时未支护
5.	暗挖支护-超时未支护
6.	暗挖支护-钢格栅间距不满足要求
7.	违规动火-防火间距不满足要求
8.	违规动火-看火人脱岗
9.	违规动火-周边未配备消防器材
10.	违规动火-无动火证动火
11.	违规动火-非特种工动火
12.	地下作业面-渗漏水
13.	地下作业面-涌水涌沙
14.	地下作业面-掌子面土体坍塌
"""
camera_alarm_data_dict = {
    "model": "",        # string 枪机1 球机2 半球3
    "brand": "",        # string 
    "equipmentId": "",  # string
    "alarmType": "",    # string
    "alarmImage": "",   # base64
    "alarmUrl": "",     # string
    "name": "",         # string
    "time": "",         # string
    "gongdiSN": "",     # string
    "latitude": "",     # string
    "longitude": "",    # string
    "alarmInfo": "",    # string
    "md5Check": "",     # string
}

alarm_image_save_path = 'outs/alarm_images'
playback_save_path = 'outs/playback'
text_font_path = '/home/user/bjtu/bjsubway/resources/Deng.ttf'

post_time_interval = {'fire': 60. * 1, 
                      'pipe': 60. * 60 * 8, 
                      'tunnel': 60. * 3, 
                      }
