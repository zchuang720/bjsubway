"""
names:
    0: grid         # 栅格

events:
    5.	暗挖支护-超时未支护
    6.	暗挖支护-钢格栅间距不满足要求
    18.	暗挖未及时喷射混凝土
"""

from enum import Enum, auto


grid_alarm_result = {
    'refine_result': None,
    'display_info': None,
}

# 标签类别
id_person = 0
id_working_face = 1
id_steel = 2
id_truck = 3

class Event (Enum):
    # 事件类型
    hasHole = auto()
    noHole = auto()
    hasCar = auto()
    noCar = auto()
    noCar_aboveThresh_noPerson = auto()
    noCar_aboveThresh_hasPerson = auto()

event_timeout = {
    Event.hasHole: 60,
    Event.noCar: 30 * 1 * 1,
    Event.noCar_aboveThresh_hasPerson: 30
}


translated_cls_name = {
    id_steel: '钢架',
    id_person: '人',
    id_working_face: '挖面',
    id_truck: "车",
}

yolo_cls_buff_size = 3
