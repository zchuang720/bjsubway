import copy

import util
import properties

'''
动火:
192.101.4.226 新龙泽站-主体基坑西区-北墙-013 http://123.125.19.139:6101/stream/fire/192.101.4.226
192.168.1.234 安全管理-新龙泽站-轨道公司演示002 http://123.125.19.139:6101/stream/fire/192.168.1.234
192.168.1.213 安全管理-新龙泽站-主体-可见光检测-001 http://123.125.19.139:6101/stream/fire/192.168.1.213
钢支撑:
192.101.4.234 新龙泽站-主体基坑西区-南墙-009 http://123.125.19.139:6101/stream/pipe/192.101.4.234
192.101.4.235 新龙泽站-主体基坑西区-南墙-008 http://123.125.19.139:6101/stream/pipe/192.101.4.235
192.101.4.225 新龙泽站-主体基坑西区-北墙-012 http://123.125.19.139:6101/stream/pipe/192.101.4.225
192.101.4.228 新龙泽站-主体基坑西区-北墙-014 http://123.125.19.139:6101/stream/pipe/192.101.4.228
'''
cams_need_added = [
    {
        # 'cameraUrl': 'http://123.125.19.139:6101/stream/fire/192.101.4.226',
        'cameraUrl': 'http://123.125.19.139:6101/stream/fire/192.101.4.235',
        'equipmentId': 'fire-192.101.4.226',
        'name': '动火-新龙泽站-主体基坑西区-北墙-013',
    },
    {
        'cameraUrl': 'http://123.125.19.139:6101/stream/fire/192.168.1.234',
        'equipmentId': 'fire-192.168.1.234',
        'name': '动火-安全管理-新龙泽站-轨道公司演示002',
    },
    {
        'cameraUrl': 'http://123.125.19.139:6101/stream/fire/192.168.1.213',
        'equipmentId': 'fire-192.168.1.213',
        'name': '动火-安全管理-新龙泽站-主体-可见光检测-001',
    },
    {
        'cameraUrl': 'http://123.125.19.139:6101/stream/fire/192.101.4.235',
        'equipmentId': 'fire-192.101.4.235',
        'name': '动火-新龙泽站-主体基坑西区-南墙-008',
    },
    {
        'cameraUrl': 'http://123.125.19.139:6101/stream/pipe/192.101.4.231',
        'equipmentId': 'pipe-192.101.4.231',
        'name': '钢支撑-新龙泽站-主体基坑西区-南墙-004',
    },
    {
        'cameraUrl': 'http://123.125.19.139:6101/stream/pipe/192.101.4.234',
        'equipmentId': 'pipe-192.101.4.234',
        'name': '钢支撑-新龙泽站-主体基坑西区-南墙-009',
    },
    {
        'cameraUrl': 'http://123.125.19.139:6101/stream/pipe/192.101.4.235',
        'equipmentId': 'pipe-192.101.4.235',
        'name': '钢支撑-新龙泽站-主体基坑西区-南墙-008',
    },
    {
        'cameraUrl': 'http://123.125.19.139:6101/stream/pipe/192.101.4.225',
        'equipmentId': 'pipe-192.101.4.225',
        'name': '钢支撑-新龙泽站-主体基坑西区-北墙-012',
    },
    {
        'cameraUrl': 'http://123.125.19.139:6101/stream/pipe/192.101.4.228',
        'equipmentId': 'pipe-192.101.4.228',
        'name': '钢支撑-新龙泽站-主体基坑西区-北墙-014',
    },
]


def add_cam_post():
    for cam in cams_need_added:
        post_data = copy.deepcopy(properties.post_data_dict)
        post_data["equipment_type"] = "camera"
        post_data["event_type"] = "add"

        camera_add_data = {}
        camera_add_data["model"] = "2"
        camera_add_data["cameraUrl"] = ""
        camera_add_data["controlUrl"] = ""
        camera_add_data["brand"] = "久译"
        camera_add_data["equipmentId"] = ""
        camera_add_data["name"] = ""
        camera_add_data["sipSN"] = ""
        camera_add_data["gongdiSN"] = properties.gongdiSN
        camera_add_data["latitude"] = ""
        camera_add_data["longitude"] = ""
        camera_add_data["location"] = ""
        camera_add_data["contacts"] = ""
        camera_add_data["contactsPhone"] = ""
        camera_add_data["serverIP"] = ""
        camera_add_data["serverPort"] = ""
        camera_add_data["userName"] = ""
        camera_add_data["userPwd"] = ""

        camera_add_data.update(cam)

        camera_add_data["md5Check"] = util.generate_md5_checksum(
                                            camera_add_data["cameraUrl"] + camera_add_data["equipmentId"] \
                                            + properties.md5_salt)
        post_data["data"].append(camera_add_data)

        print(post_data)
        util.post(properties.post_addr, post_data)


if __name__ == "__main__":
    add_cam_post()
