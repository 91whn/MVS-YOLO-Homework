import sys
import os
import cv2
import numpy as np
from ctypes import *
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'MvImport'))
from MvCameraControl_class import *
from CameraParams_header import *

os.environ['MVCAM_COMMON_RUNENV'] = '/opt/MVS/lib'
os.environ['LD_LIBRARY_PATH'] = '/opt/MVS/lib/64:' + os.environ.get('LD_LIBRARY_PATH', '')

def main():
    deviceList = MV_CC_DEVICE_INFO_LIST()
    MvCamera.MV_CC_EnumDevices(MV_USB_DEVICE, deviceList)
    
    cam = MvCamera()
    stDeviceList = cast(deviceList.pDeviceInfo[0], POINTER(MV_CC_DEVICE_INFO)).contents
    cam.MV_CC_CreateHandle(stDeviceList)
    cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
    
    # 确保处于连续采集模式
    cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
    
    stParam = MVCC_INTVALUE_EX()
    cam.MV_CC_GetIntValueEx("PayloadSize", stParam)
    nPayloadSize = stParam.nCurValue
    cam.MV_CC_StartGrabbing()

    data_buf = (c_ubyte * nPayloadSize)()
    stFrameInfo = MV_FRAME_OUT_INFO_EX()

    print("🎉 任务3：格式与性能测试开始！")
    print("请观察终端输出的 FPS 和转换耗时。按 [Q] 退出。")
    print("👉 建议现在打开一个新的终端窗口，输入 'htop' 查看 CPU 占用率。")

    frame_count = 0
    start_time = time.time()
    total_convert_time = 0
    convert_frames = 0
    fps = 0.0

    while True:
        ret = cam.MV_CC_GetOneFrameTimeout(data_buf, nPayloadSize, stFrameInfo, 1000)
        if ret == 0:
            frame_count += 1
            
            # 每秒计算一次原始 FPS
            current_time = time.time()
            if current_time - start_time >= 1.0:
                fps = frame_count / (current_time - start_time)
                print(f"实时 FPS: {fps:.2f}")
                frame_count = 0
                start_time = current_time
            
            # 测量 Bayer 转 BGR 的耗时
            t1 = time.time()
            
            image = np.frombuffer(data_buf, dtype=np.uint8, count=nPayloadSize)
            if stFrameInfo.enPixelType == 17301513: # BayerRG8
                image_2d = image.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
                bgr_image = cv2.cvtColor(image_2d, cv2.COLOR_BayerRG2BGR)
            else:
                image_2d = image.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
                bgr_image = cv2.cvtColor(image_2d, cv2.COLOR_GRAY2BGR)
                
            t2 = time.time()
            convert_time_ms = (t2 - t1) * 1000
            total_convert_time += convert_time_ms
            convert_frames += 1

            # 每 30 帧打印一次平均转换时间
            if convert_frames == 30:
                avg_time = total_convert_time / 30
                print(f"📊 图像格式转换耗时: {avg_time:.2f} ms")
                total_convert_time = 0
                convert_frames = 0

            cv2.putText(bgr_image, f"FPS: {fps:.1f}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Task 3 - Performance", bgr_image)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

    cam.MV_CC_StopGrabbing()
    cam.MV_CC_CloseDevice()
    cam.MV_CC_DestroyHandle()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
