import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import properties


def check_person_state(pred_result):
    # 判断是否有人
    return 1 in pred_result.boxes.cls

def check_steel_state(pred_result):
    # 判断是否有钢架
    return 0 in pred_result.boxes.cls

def check_woking_face_state(pred_result):
    # 判断是否有开挖面
    return 2 in pred_result.boxes.cls


def draw_text(img, text, left=0, top=0, textColor=(255, 255, 255), textSize=50):
    # 判断是否为opencv图片类型
    if (isinstance(img, np.ndarray)):
        img = Image.fromarray(img)
    draw = ImageDraw.Draw(img)
    fontText = ImageFont.truetype(properties.text_font_path, textSize, encoding="utf-8")
    linewidth = textSize + 40

    for t in text:
        draw.rectangle((left, top, left+600, top+linewidth), fill=(0,0,255), outline=(0,0,255))
        draw.text((left+20, top+20), t, textColor, font=fontText)
        top += linewidth

    return np.asarray(img)

