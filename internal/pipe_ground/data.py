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
}


id_anchor = 0
id_installed_pipe = 1
id_ground = 2
id_pipe_bottom = 3
id_target_anchor = 4

translated_cls_name = {
    id_anchor: '托盘',
    id_installed_pipe: '已支护',
    id_ground: '反压土',
    id_pipe_bottom: '钢支撑',
    id_target_anchor: '托盘',
}


timer_duration = 100