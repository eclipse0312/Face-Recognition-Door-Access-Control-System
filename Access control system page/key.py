import cv2
import numpy as np
import matplotlib.pyplot as plt

# 设置默认字体为SimHei
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

def display_gray_and_equalized_images(image_path):
    # 读取图像
    image = cv2.imread(image_path)

    # 将图像转换为灰度图像
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 直方图均衡化
    equalized_image = cv2.equalizeHist(gray_image)

    # 显示原始图像、灰度化图像和直方图均衡化后的图像
    plt.figure(figsize=(10, 5))

    plt.subplot(2, 3, 1)
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title('原始图像')
    plt.axis('off')

    plt.subplot(2, 3, 2)
    plt.imshow(gray_image, cmap='gray')
    plt.title('灰度化图像')
    plt.axis('off')

    plt.subplot(2, 3, 3)
    plt.imshow(equalized_image, cmap='gray')
    plt.title('直方图均衡化图像')
    plt.axis('off')

    # 显示原始图像、灰度图像和直方图均衡化图像的直方图
    plt.subplot(2, 3, 4)
    plt.hist(image.ravel(), bins=256, color='blue', alpha=0.7)
    plt.title('原始图像直方图')
    plt.xlabel('像素值')
    plt.ylabel('频率')

    plt.subplot(2, 3, 5)
    plt.hist(gray_image.ravel(), bins=256, color='blue', alpha=0.7)
    plt.title('灰度化图像直方图')
    plt.xlabel('像素值')
    plt.ylabel('频率')

    plt.subplot(2, 3, 6)
    plt.hist(equalized_image.ravel(), bins=256, color='blue', alpha=0.7)
    plt.title('直方图均衡化图像直方图')
    plt.xlabel('像素值')
    plt.ylabel('频率')

    plt.tight_layout()
    plt.savefig('D:/HXT/毕设周报视频/毕业设计/毕业设计图片/image.png', dpi=600)
    plt.show()

# 用你的图片路径替换这里的路径
image_path ="D:\HXT\FRpython\\face\hexitong.jpg"

# 显示灰度化和直方图均衡化的图片以及直方图
display_gray_and_equalized_images(image_path)


