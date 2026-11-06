import sys
import os
import cv2
import numpy as np
from ctypes import *
import time
from ultralytics import YOLO

sys.path.append(os.path.join(os.path.dirname(__file__), 'MvImport'))
from MvCameraControl_class import *
from CameraParams_header import *

os.environ['MVCAM_COMMON_RUNENV'] = '/opt/MVS/lib'
os.environ['LD_LIBRARY_PATH'] = '/opt/MVS/lib/64:' + os.environ.get('LD_LIBRARY_PATH', '')

# 这里是你刚刚放好的真实模型路径
MODEL_PATH = "/home/wanghaonan/mvs_homework/best.pt"  

def main():
    print(f"正在加载YOLO模型: {MODEL_PATH} ...")
    try:
        model = YOLO(MODEL_PATH)
        print("✅ 模型加载成功！")
    except Exception as e:
        print(f"❌ 模型加载失败，请检查路径或是否安装了ultralytics: {e}")
        return

    print("正在连接USB相机...")
    cam = MvCamera()
    deviceList = MV_CC_DEVICE_INFO_LIST()
    MvCamera.MV_CC_EnumDevices(MV_USB_DEVICE, deviceList)
    stDeviceList = cast(deviceList.pDeviceInfo[0], POINTER(MV_CC_DEVICE_INFO)).contents
    cam.MV_CC_CreateHandle(stDeviceList)
    cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
    
    stParam = MVCC_INTVALUE_EX()
    cam.MV_CC_SetFloatValue("ExposureTime", 15000.0)
    cam.MV_CC_GetIntValueEx("PayloadSize", stParam)
    nPayloadSize = stParam.nCurValue
    cam.MV_CC_StartGrabbing()
    print("✅ 相机启动成功，开始实时推理！按 Q 退出。")

    data_buf = (c_ubyte * nPayloadSize)()
    stFrameInfo = MV_FRAME_OUT_INFO_EX()
    prev_time = time.time()

    while True:
        ret = cam.MV_CC_GetOneFrameTimeout(data_buf, nPayloadSize, stFrameInfo, 1000)
        if ret == 0:
            image = np.frombuffer(data_buf, dtype=np.uint8, count=nPayloadSize)
            
            # 图像格式转换
            if stFrameInfo.enPixelType == 17301513: # BayerRG8
                image_2d = image.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
                bgr_image = cv2.cvtColor(image_2d, cv2.COLOR_BayerRG2BGR)
            else:
                image_2d = image.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
                bgr_image = cv2.cvtColor(image_2d, cv2.COLOR_GRAY2BGR)

            # YOLO 推理
            results = model(bgr_image, verbose=False)
            
            # 画框和显示信息
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = f"{model.names[cls]} {conf:.2f}"

                    cv2.rectangle(bgr_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.circle(bgr_image, (cx, cy), 4, (0, 0, 255), -1)
                    cv2.putText(bgr_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.putText(bgr_image, f"({cx},{cy})", (cx - 40, cy + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                    
                    print(f"识别: {label} | 坐标: ({cx}, {cy})")

            # 显示 FPS
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time)
            prev_time = curr_time
            cv2.putText(bgr_image, f"FPS: {fps:.1f}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            cv2.imshow("YOLO Real-time Detection", bgr_image)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

    cam.MV_CC_StopGrabbing()
    cam.MV_CC_CloseDevice()
    cam.MV_CC_DestroyHandle()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

