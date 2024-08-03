from ultralytics import YOLO
import cv2
import numpy as np
import matplotlib as plt

import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'


# plt.rcParams['font.sans-serif'] = ['SimHei']
# plt.rcParams['axes.unicode_minus'] = False


if __name__=='__main__':

# Load a model
    model_name = 'yolov8l-seg'
    model = YOLO(f"{model_name}.yaml") # build a new model from scratch
    model = YOLO(f"/home/user/bjtu/bjsubway/runs/segment/train3/weights/last.pt") # load a pretrained model (recommended for training)3
    # model = YOLO("./best.pt")

    model.train(data=r'/home/user/bjtu/datasets/tunnel_0422/config.yaml', imgsz=1280,device=[0,1], epochs=100, workers=16, batch=16)
    # metrics = model.val() # evaluate model performance on the validation set