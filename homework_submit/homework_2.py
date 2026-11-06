import sys
import os
import cv2
import numpy as np
from ctypes import *
sys.path.append(os.path.join(os.path.dirname(__file__), 'MvImport'))
from MvCameraControl_class import *
from CameraParams_header import *

os.environ['MVCAM_COMMON_RUNENV'] = '/opt/MVS/lib'
os.environ['LD_LIBRARY_PATH'] = '/opt/MVS/lib/64:' + os.environ.get('LD_LIBRARY_PATH', '')

# 定义增益选项 (dB)
gains = [0.0, 6.0, 12.0]
current_gain_idx = 0

def main():
    global current_gain_idx
    deviceList = MV_CC_DEVICE_INFO_LIST()
    MvCamera.MV_CC_EnumDevices(MV_USB_DEVICE, deviceList)
    
    cam = MvCamera()
    stDeviceList = cast(deviceList.pDeviceInfo[0], POINTER(MV_CC_DEVICE_INFO)).contents
    cam.MV_CC_CreateHandle(stDeviceList)
    cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)

    # 作业要求：保持曝光不变（设为 1000us）
    cam.MV_CC_SetFloatValue("ExposureTime", 1000.0)

    stParam = MVCC_INTVALUE_EX()
    cam.MV_CC_GetIntValueEx("PayloadSize", stParam)
    nPayloadSize = stParam.nCurValue
    cam.MV_CC_StartGrabbing()

    print("🎉 增益测试开始！(曝光固定为 1000us)")
    print("按 [1] 增益 0 dB | 按 [2] 增益 6 dB | 按 [3] 增益 12 dB")
    print("按 [S] 保存当前图 | 按 [Q] 退出")

    cam.MV_CC_SetFloatValue("Gain", gains[current_gain_idx])

    data_buf = (c_ubyte * nPayloadSize)()
    stFrameInfo = MV_FRAME_OUT_INFO_EX()

    while True:
        ret = cam.MV_CC_GetOneFrameTimeout(data_buf, nPayloadSize, stFrameInfo, 1000)
        if ret == 0:
            image = np.frombuffer(data_buf, dtype=np.uint8, count=nPayloadSize)
            
            if stFrameInfo.enPixelType == 17301513:
                image_2d = image.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
                bgr_image = cv2.cvtColor(image_2d, cv2.COLOR_BayerRG2BGR)
            else:
                image_2d = image.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
                bgr_image = cv2.cvtColor(image_2d, cv2.COLOR_GRAY2BGR)

            # 核心：统计饱和像素（灰度值 >= 250）的比例
            gray_img = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
            saturated_pixels = np.sum(gray_img >= 250)
            total_pixels = gray_img.size
            sat_ratio = (saturated_pixels / total_pixels) * 100

            # 在画面上显示当前增益和过曝比例
            text_gain = f"Gain: {gains[current_gain_idx]} dB"
            text_ratio = f"Saturated: {sat_ratio:.2f}%"
            cv2.putText(bgr_image, text_gain, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(bgr_image, text_ratio, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            cv2.imshow("MVS Gain Test", bgr_image)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27: 
                break
            elif key == ord('1'):
                current_gain_idx = 0
                cam.MV_CC_SetFloatValue("Gain", gains[0])
                print(f"-> 增益设为 {gains[0]} dB")
            elif key == ord('2'):
                current_gain_idx = 1
                cam.MV_CC_SetFloatValue("Gain", gains[1])
                print(f"-> 增益设为 {gains[1]} dB")
            elif key == ord('3'):
                current_gain_idx = 2
                cam.MV_CC_SetFloatValue("Gain", gains[2])
                print(f"-> 增益设为 {gains[2]} dB")
            elif key == ord('s'):
                filename = f"gain_{int(gains[current_gain_idx])}dB_sat_{sat_ratio:.2f}pct.jpg"
                cv2.imwrite(filename, bgr_image)
                print(f"📸 保存成功：{filename} (过曝比例: {sat_ratio:.2f}%)")

    cam.MV_CC_StopGrabbing()
    cam.MV_CC_CloseDevice()
    cam.MV_CC_DestroyHandle()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

