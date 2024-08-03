"""
names:
    0: grid         # 栅格

events:
    5.	暗挖支护-超时未支护
    6.	暗挖支护-钢格栅间距不满足要求
    18.	暗挖未及时喷射混凝土
"""

grid_alarm_result = {
    'refine_result': None,
    'display_info': None,
}

# 标签类别
id_steel = 0
id_person = 1
id_working_face = 2
id_truck = 4

# 事件类型
event_finish_dig = 1
event_doing_dig = 2
event_stop_working = 3

event_timeout = {
    event_finish_dig: 60,
    event_doing_dig: 60 * 60 * 2,
    event_stop_working: 60
}


translated_cls_name = {
    id_steel: '钢架',
    id_person: '人',
    id_working_face: '开挖面',
    id_truck: "卡车",
}

yolo_cls_buff_size = 3
