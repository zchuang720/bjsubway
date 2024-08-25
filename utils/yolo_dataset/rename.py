import os
import random

# 指定要重命名文件的文件夹路径
folder_path = r"datasets\fire-tunnel-v1"  # 替换为你的文件夹路径

# 获取文件夹中所有文件的列表
file_list = os.listdir(folder_path)
# random.shuffle(file_list)

# 初始化序号
count = 1

# 遍历文件列表
for old_name in file_list:
    # 构建新的文件名，使用递增的序号并保留原文件扩展名
    file_extension = os.path.splitext(old_name)[1]
    new_name = f"{count:04d}{file_extension}"  # 4位序号，前面补零

    # 构建文件的完整路径
    old_path = os.path.join(folder_path, old_name)
    new_path = os.path.join(folder_path, new_name)

    # 重命名文件
    os.rename(old_path, new_path)

    # 递增序号
    count += 1

print("文件重命名完成")
