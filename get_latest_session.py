import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangodemo.settings')
django.setup()

from wxapp.models import DataCollectionSession

def get_latest_sessions():
    """获取最新的会话"""
    sessions = DataCollectionSession.objects.all().order_by('-id')[:10]
    
    print("最新的10个会话:")
    for session in sessions:
        print(f"  会话 {session.id}: {session.status} (设备组: {session.device_group.group_code})")
    
    # 获取活跃会话
    active_sessions = DataCollectionSession.objects.filter(status__in=['calibrating', 'collecting']).order_by('-id')
    print(f"\n活跃会话 (calibrating/collecting):")
    for session in active_sessions:
        print(f"  会话 {session.id}: {session.status} (设备组: {session.device_group.group_code})")

if __name__ == "__main__":
    get_latest_sessions() 