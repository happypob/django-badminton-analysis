import os
import django
import requests
import json

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangodemo.settings')
django.setup()

from wxapp.models import DataCollectionSession, DeviceGroup, WxUser

def create_test_session_for_esp32():
    """为ESP32创建一个新的测试会话"""
    
    # 获取或创建设备组
    device_group, created = DeviceGroup.objects.get_or_create(group_code="esp32_test_group")
    
    # 获取或创建测试用户
    wx_user, created = WxUser.objects.get_or_create(openid="esp32_test_user")
    
    # 创建新的采集会话
    session = DataCollectionSession.objects.create(
        device_group=device_group,
        user=wx_user,
        status='calibrating'  # 从calibrating开始
    )
    
    print(f"✅ 创建了新的测试会话:")
    print(f"  会话ID: {session.id}")
    print(f"  状态: {session.status}")
    print(f"  设备组: {session.device_group.group_code}")
    print(f"  用户: {session.user.openid}")
    
    return session

def test_esp32_upload_with_session(session_id):
    """测试ESP32上传到指定会话"""
    
    url = "http://47.122.129.159:8000/wxapp/esp32/upload/"
    
    test_data = {
        "device_code": "esp32s3_multi_001",
        "sensor_type": "waist",
        "session_id": str(session_id),
        "data": json.dumps({
            "acc": [1.23, 2.34, 3.45],
            "gyro": [4.56, 5.67, 6.78],
            "angle": [7.89, 8.90, 9.01]
        }),
        "timestamp": "1234567890",
        "streaming": "true"
    }
    
    print(f"\n测试ESP32上传到会话 {session_id}:")
    try:
        response = requests.post(url, data=test_data)
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text}")
        
        if response.status_code == 200:
            print("✅ 上传成功!")
            return True
        else:
            print("❌ 上传失败!")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

if __name__ == "__main__":
    # 创建新的测试会话
    session = create_test_session_for_esp32()
    
    # 测试ESP32上传
    success = test_esp32_upload_with_session(session.id)
    
    if success:
        print(f"\n🎉 ESP32可以使用会话ID {session.id} 进行流式传输!")
        print(f"请将ESP32代码中的session_id修改为: {session.id}")
    else:
        print(f"\n❌ ESP32上传测试失败，需要进一步调试") 