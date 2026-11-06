import sys
import os
from ctypes import *
sys.path.append(os.path.join(os.path.dirname(__file__), 'MvImport'))
from MvCameraControl_class import *

# 强制设置海康动态库路径，防止报错
os.environ['MVCAM_COMMON_RUNENV'] = '/opt/MVS/lib'
os.environ['LD_LIBRARY_PATH'] = '/opt/MVS/lib/64:' + os.environ.get('LD_LIBRARY_PATH', '')

def test_camera():
    print("1. 正在强制通过IP 192.168.199.128 连接相机...")
    
    # 跳过自动搜索，直接指定相机的IP
    cam = MvCamera()
    stDeviceList = MV_CC_DEVICE_INFO()
    stDeviceList.nTLayerType = MV_GIGE_DEVICE
    
    # 将IP转换为十六进制填入
    ip_bytes = list(map(int, "192.168.199.128".split('.')))
    stDeviceList.SpecialInfo.stGigEInfo.nCurrentIp = (ip_bytes[0] << 24) | (ip_bytes[1] << 16) | (ip_bytes[2] << 8) | ip_bytes[3]

    ret = cam.MV_CC_CreateHandle(stDeviceList)
    if ret != 0:
        print(f"❌ 创建句柄失败! 错误码: {ret}")
        return
        
    ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
    if ret != 0:
        print(f"❌ 打开相机失败! 错误码: {ret}")
        return
        
    print("✅ 相机连接成功！正在尝试获取图像流...")
    
    ret = cam.MV_CC_StartGrabbing()
    if ret != 0:
        print(f"❌ 开启取流失败! 错误码: {ret}")
    else:
        print("🎉 开启取流成功！相机已经在传数据了！")
            
    # 释放资源
    cam.MV_CC_StopGrabbing()
    cam.MV_CC_CloseDevice()
    cam.MV_CC_DestroyHandle()

if __name__ == "__main__":
    test_camera()
