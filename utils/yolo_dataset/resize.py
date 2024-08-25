import os
import cv2

# 指定要处理的文件夹路径
folder_path = r"datasets\fire2\orig_img"  # 替换为你的文件夹路径

# 获取文件夹中所有文件的列表
file_list = os.listdir(folder_path)

# 遍历文件列表
for file_name in file_list:
    # 构建文件的完整路径
    file_path = os.path.join(folder_path, file_name)

    # 检查文件是否为图片（假设处理的是常见图片格式）
    if file_name.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif")):
        # 读取图片
        image = cv2.imread(file_path)

        # 获取图片的宽度和高度
        height, width, _ = image.shape

        # 缩小图片
        resized_image = cv2.resize(image, (0, 0), fx=1, fy=1)

        # 构建新的文件名，将图片保存为 JPG 格式
        new_name = os.path.splitext(file_name)[0] + ".jpg"

        # 构建保存文件的完整路径
        new_path = os.path.join(folder_path, new_name)

        # 保存缩小后的图片
        cv2.imwrite(new_path, resized_image)

print("图片缩小并保存完成")
