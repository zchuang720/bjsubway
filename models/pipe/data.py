"""
names:
    0: anchor
    1: pipe
    2: installed_pipe

events:
    4.	明挖支护-超时未支护
"""

pipe_alarm_result = {
    'refine_result': None,
    'display_info': None,
    'polygon': None,
}

bounding_dist_threshold = 0.2

polygon_dict = {
    # "MainProcess": [[750/2336,600/1752], [1400/2336,600/1752], [1650/2336,1500/1752], [150/2336,1500/1752]],
    "pipe-1": [[750/2336,600/1752], [1400/2336,600/1752], [1650/2336,1500/1752], [150/2336,1500/1752]],
    "pipe-2": [[750/2336,600/1752], [1400/2336,600/1752], [1650/2336,1500/1752], [150/2336,1500/1752]],
    "pipe-3": [[750/2336,600/1752], [1400/2336,600/1752], [1650/2336,1500/1752], [150/2336,1500/1752]],
    "pipe-4": [[750/2336,600/1752], [1400/2336,600/1752], [1650/2336,1500/1752], [150/2336,1500/1752]],
    "pipe-钢支撑01": [[10/1920,400/1080], [1400/1920,300/1080], [1900/1920,370/1080], [1900/1920,1050/1080], [10/1920,1050/1080]],
    "pipe-钢支撑02": [[10/1920,400/1080], [1110/1920,300/1080], [1900/1920,370/1080], [1900/1920,1050/1080], [10/1920,1050/1080]],
}

translated_cls_name = {
    0: '托盘',
    1: '钢支撑',
    2: '已支护',
}

translated_cls_name_2 = {
    0: '未支护',
    1: '已支护',
    2: '未支护钢支撑',
}
