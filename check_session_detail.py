import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangodemo.settings')
django.setup()

from wxapp.models import DataCollectionSession, SensorData

def check_session_detail(session_id):
    """详细检查会话状态"""
    try:
        session = DataCollectionSession.objects.get(id=session_id)
        print(f"会话 {session_id} 详细信息:")
        print(f"  ID: {session.id}")
        print(f"  状态: {session.status}")
        print(f"  开始时间: {session.start_time}")
        print(f"  结束时间: {session.end_time}")
        print(f"  设备组: {session.device_group.group_code}")
        print(f"  用户: {session.user.openid}")
        
        # 检查该会话的传感器数据
        sensor_data_count = SensorData.objects.filter(session=session).count()
        print(f"  传感器数据数量: {sensor_data_count}")
        
        if sensor_data_count > 0:
            sensor_types = SensorData.objects.filter(session=session).values_list('sensor_type', flat=True).distinct()
            print(f"  传感器类型: {list(sensor_types)}")
            
            # 显示最近的数据
            recent_data = SensorData.objects.filter(session=session).order_by('-timestamp')[:5]
            print(f"  最近5条数据:")
            for data in recent_data:
                print(f"    {data.timestamp}: {data.sensor_type} - {data.device_code}")
        
        return session
    except DataCollectionSession.DoesNotExist:
        print(f"❌ 会话 {session_id} 不存在!")
        return None

def test_session_api(session_id):
    """测试会话API"""
    import requests
    
    url = "http://47.122.129.159:8000/wxapp/esp32/upload/"
    
    test_data = {
        "device_code": "esp32s3_multi_001",
        "sensor_type": "waist",
        "session_id": str(session_id),
        "data": '{"acc":[1,2,3],"gyro":[4,5,6],"angle":[7,8,9]}',
        "timestamp": "1234567890",
        "streaming": "true"
    }
    
    print(f"\n测试会话 {session_id} 的API:")
    try:
        response = requests.post(url, data=test_data)
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text}")
    except Exception as e:
        print(f"  API测试失败: {e}")

if __name__ == "__main__":
    # 检查会话1009
    check_session_detail(1009)
    test_session_api(1009)
    
    # 检查会话8 (calibrating状态)
    print("\n" + "="*50)
    check_session_detail(8)
    test_session_api(8) 