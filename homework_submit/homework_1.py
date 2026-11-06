import sys
import os
import cv2
import numpy as np
from ctypes import *
sys.path.append(os.path.join(os.path.dirname(__file__), 'MvImport'))
from MvCameraControl_class import *
from CameraParams_header import *

# 强制设置环境变量（保险起见）
os.environ['MVCAM_COMMON_RUNENV'] = '/opt/MVS/lib'
os.environ['LD_LIBRARY_PATH'] = '/opt/MVS/lib/64:' + os.environ.get('LD_LIBRARY_PATH', '')

# 定义曝光时间
exposure_times = [500.0, 1000.0, 3000.0]
current_idx = 1 # 默认 1000us

def main():
    global current_idx
    
    print("1. 正在连接 USB 相机...")
    deviceList = MV_CC_DEVICE_INFO_LIST()
    ret = MvCamera.MV_CC_EnumDevices(MV_USB_DEVICE, deviceList)
    if ret != 0 or deviceList.nDeviceNum == 0:
        print("❌ 找不到相机！")
        return

    cam = MvCamera()
    stDeviceList = cast(deviceList.pDeviceInfo[0], POINTER(MV_CC_DEVICE_INFO)).contents

    cam.MV_CC_CreateHandle(stDeviceList)
    cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)

    # 获取图像大小信息
    stParam = MVCC_INTVALUE_EX()
    cam.MV_CC_GetIntValueEx("PayloadSize", stParam)
    nPayloadSize = stParam.nCurValue

    # 开始取流
    cam.MV_CC_StartGrabbing()
    print("🎉 开始取流！请在弹出的窗口中操作：")
    print("按 [1] 设置 500us | 按 [2] 设置 1000us | 按 [3] 设置 3000us")
    print("按 [S] 保存当前图片 | 按 [Q] 或 [ESC] 退出程序")

    # 提前设置好默认曝光
    cam.MV_CC_SetFloatValue("ExposureTime", exposure_times[current_idx])

    data_buf = (c_ubyte * nPayloadSize)()
    stFrameInfo = MV_FRAME_OUT_INFO_EX()

    while True:
        # 获取一帧图像
        ret = cam.MV_CC_GetOneFrameTimeout(data_buf, nPayloadSize, stFrameInfo, 1000)
        
        if ret == 0:
            # 将 C 语言的内存数据转为 numpy 数组
            image = np.frombuffer(data_buf, dtype=np.uint8, count=stFrameInfo.nFrameLen)
            
            # 打印真实的像素格式
            print(f"当前像素格式代码: {stFrameInfo.enPixelType}, 图像长度: {stFrameInfo.nFrameLen}")
            
            # 判断像素格式并转换 (MV-CA016-10UC 通常是 BayerRG8 或 Mono8)
            if stFrameInfo.enPixelType == PixelType_Gvsp_BayerRG8:
                # 先reshape成二维
                image_2d = image.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
                # 使用 OpenCV 转换为 BGR 用于显示
                bgr_image = cv2.cvtColor(image_2d, cv2.COLOR_BayerRG2BGR)
            elif stFrameInfo.enPixelType == PixelType_Gvsp_Mono8:
                image_2d = image.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
                bgr_image = cv2.cvtColor(image_2d, cv2.COLOR_GRAY2BGR)
            else:
                # 其他格式简单处理，防止报错
                image_2d = image.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
                bgr_image = cv2.cvtColor(image_2d, cv2.COLOR_GRAY2BGR)

            # 在画面上显示当前曝光时间
            cv2.putText(bgr_image, f"Exposure: {exposure_times[current_idx]} us", (10, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # 显示图像
            cv2.imshow("MVS USB Camera", bgr_image)

            # 键盘按键监听
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27: # q 或 ESC 退出
                break
            elif key == ord('1'):
                current_idx = 0
                cam.MV_CC_SetFloatValue("ExposureTime", exposure_times[0])
                print(f"-> 曝光已设为 {exposure_times[0]} us")
            elif key == ord('2'):
                current_idx = 1
                cam.MV_CC_SetFloatValue("ExposureTime", exposure_times[1])
                print(f"-> 曝光已设为 {exposure_times[1]} us")
            elif key == ord('3'):
                current_idx = 2
                cam.MV_CC_SetFloatValue("ExposureTime", exposure_times[2])
                print(f"-> 曝光已设为 {exposure_times[2]} us")
            elif key == ord('s'):
                filename = f"exposure_{int(exposure_times[current_idx])}us.jpg"
                cv2.imwrite(filename, bgr_image)
                print(f"📸 图片已保存：{filename}")

    # 释放资源
    print("正在释放资源...")
    cam.MV_CC_StopGrabbing()
    cam.MV_CC_CloseDevice()
    cam.MV_CC_DestroyHandle()
    cv2.destroyAllWindows()
    print("程序安全退出。")

if __name__ == "__main__":
    main()

