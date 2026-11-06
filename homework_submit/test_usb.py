import sys
import os
from ctypes import *
sys.path.append(os.path.join(os.path.dirname(__file__), 'MvImport'))
from MvCameraControl_class import *

def test_usb():
    print("1. 正在查找 USB 相机...")
    deviceList = MV_CC_DEVICE_INFO_LIST()
    ret = MvCamera.MV_CC_EnumDevices(MV_USB_DEVICE, deviceList)
    
    if ret != 0 or deviceList.nDeviceNum == 0:
        print("❌ 找不到 USB 相机！")
        return
    print(f"✅ 成功找到 {deviceList.nDeviceNum} 个 USB 相机！")

    cam = MvCamera()
    stDeviceList = cast(deviceList.pDeviceInfo[0], POINTER(MV_CC_DEVICE_INFO)).contents

    print("2. 正在打开相机...")
    ret = cam.MV_CC_CreateHandle(stDeviceList)
    if ret != 0:
        print(f"❌ 创建句柄失败: {hex(ret)}")
        return

    ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
    if ret != 0:
        print(f"❌ 打开相机失败! 错误码: {hex(ret)}")
        return
    print("🎉 USB相机打开成功！可以开始写作业了！")

    cam.MV_CC_CloseDevice()
    cam.MV_CC_DestroyHandle()

if __name__ == "__main__":
    test_usb()

