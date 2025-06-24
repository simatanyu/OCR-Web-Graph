from picamera2 import Picamera2
from libcamera import controls
from datetime import datetime
import os
import time
from PIL import Image

# 配置路径
save_directory = "/home/dirpi/third/TestLib"
capture_interval = 2  # 1秒间隔
max_images = 100  # 最多存储 100 张图片

# 确保目录存在
os.makedirs(save_directory, exist_ok=True)

# 初始化相机
picam2 = Picamera2()
config = picam2.create_still_configuration(main={"size": (640, 480), "format": "RGB888"})
picam2.configure(config)
picam2.start()

# 设置参数（曝光、增益、白平衡）
picam2.set_controls({
    "AeEnable": True,
    #"AnalogueGain": int(1),  # 适当提升亮度，避免高噪声
    "AeMeteringMode": int(1),
    #"FrameDurationLimits": (10,30)
    "AwbMode": 1  # 设定白平衡为荧光灯模式，减少偏色
})

print(f"Capturing images in {save_directory}... Use Ctrl+C to stop.")

try:
    while True:
        # 拍摄图片
        image = picam2.capture_array()

        # 生成时间戳文件名
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{timestamp}.jpg"
        file_path = os.path.join(save_directory, filename)

        # 保存图片
        im = Image.fromarray(image)
        im.save(file_path)

        print(f"Captured: {file_path}")

        # **自动删除最早的图片**
        image_files = sorted([f for f in os.listdir(save_directory) if f.endswith(".jpg")])

        if len(image_files) > max_images:
            oldest_file = os.path.join(save_directory, image_files[0])
            os.remove(oldest_file)
            print(f"Deleted oldest image: {oldest_file}")

        # 等待下次拍摄
        time.sleep(capture_interval)

except KeyboardInterrupt:
    print("\nStopping capture...")
finally:
    picam2.stop()
    print("Done")

    
    # 生成时间戳文件名
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{timestamp}.jpg"
    file_path = os.path.join(save_directory, filename)
    
    # 保存图片
    im = Image.fromarray(image)
    im.save(file_path)
    
    print(f"Captured: {file_path}")

    # **自动删除最早的图片**
    image_files = sorted([f for f in os.listdir(save_directory) if f.endswith(".jpg")])
    
    if len(image_files) > max_images:
        oldest_file = os.path.join(save_directory, image_files[0])
        os.remove(oldest_file)
        print(f"Deleted oldest image: {oldest_file}")

    # 等待下次拍摄
    time.sleep(capture_interval)

# 停止相机
picam2.stop()
print("Done")

