import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangodemo.settings')
django.setup()

from wxapp.models import DataCollectionSession, SensorData

def check_session(session_id):
    """检查会话状态"""
    try:
        session = DataCollectionSession.objects.get(id=session_id)
        print(f"会话 {session_id} 信息:")
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
        
        return session
    except DataCollectionSession.DoesNotExist:
        print(f"❌ 会话 {session_id} 不存在!")
        return None

def list_active_sessions():
    """列出所有活跃会话"""
    print("\n所有活跃会话:")
    sessions = DataCollectionSession.objects.filter(status__in=['calibrating', 'collecting']).order_by('-id')
    
    if sessions.count() == 0:
        print("  没有活跃会话")
    else:
        for session in sessions:
            print(f"  会话 {session.id}: {session.status} (设备组: {session.device_group.group_code})")

if __name__ == "__main__":
    # 检查ESP32使用的会话
    check_session(1011)
    
    # 列出所有活跃会话
    list_active_sessions() 