# BJSubway
城市轨道交通智慧工地视觉服务，来自北京市轨道交通管理建设公司合作项目。

## Features
- 适用于事件和场景监测
- 实时警报和视频推流
- 精度与性能最优的目标检测和分割模型
- 多进程监视和故障重启
- 适配多个应用场景

## 功能效果
<details>
<summary>点击展开/折叠</summary>

### 已开发场景
1. 动火场景
![img](doc/img/fire.jpg)

2. 明挖工程
![img](doc/img/pipe.jpg)

3. 暗挖工程
![img](doc/img/tunnel.jpg)

### 性能监控
1. 内存使用
![img](doc/img/mem.png)

2. 处理速率
![img](doc/img/fps.jpg)

</details>

## 依赖
Python package:
- Python >= 3.8
- OpenCV
- Pytorch

Software:
- ffmpeg            // 视频处理
- EasyDarwin        // RTSP流分发
- NodeJS & npm      // 前端

## 安装
```
pip install -r requirements.txt
```

## Usage
#### 主程序：
1. 配置 properties.py 接入视频流地址和推流地址、第三方接入系统地址
2. 启动主程序：
```
python main.py
```
测试预测视频：
```
python pred_video.py
```
训练模型：
```
python train.py
```

## 项目结构
```
.
├── doc
├── logs
├── internal            // 业务逻辑
│   ├── fire            // 动火场景
│   ├── pipe_ground     // 明挖场景
│   └── tunnel          // 暗挖场景
├── outs
│   ├── alarm_images    // 事件图片
│   └── playback        // 时间回放
├── resources           // 资源文件
├── runs                // 输出文件
├── utils               // 工具类
│   └── yolo_dataset    // yolo数据集工具
├── web
│   ├── http            // 网页前端
│   └── rtsp2web        // 转流服务
├── weights             // 模型权重
│
├── config.py           // 运行配置
├── properties.py       // 业务配置
├── handler.py          // 处理类
└── main.py
```

<!-- ## Contributing
Describe how others can contribute to the project. -->

## License
_To be determined_

## Author
Team 623 of Beijing Jiaotong University.
#### Contact: 13392406082@163.com

<!-- ## Acknowledgements
Give credit to any third-party resources or people who helped with the project. -->