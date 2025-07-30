#!/usr/bin/env python3
"""
创建测试会话脚本
用于为多传感器数据上传测试创建会话
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangodemo.settings')
django.setup()

from wxapp.models import WxUser, DeviceGroup, DataCollectionSession, User

def create_test_session():
    """创建测试会话"""
    try:
        # 创建测试用户
        test_user, created = User.objects.get_or_create(
            username='test_user',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        
        # 创建微信用户
        wx_user, created = WxUser.objects.get_or_create(
            openid='test_openid_123',
            defaults={'user': test_user}
        )
        
        # 创建设备组
        device_group, created = DeviceGroup.objects.get_or_create(
            group_code='test_group_001'
        )
        
        # 创建测试会话
        session, created = DataCollectionSession.objects.get_or_create(
            id=123,  # 固定ID用于测试
            defaults={
                'device_group': device_group,
                'user': wx_user,
                'status': 'collecting'
            }
        )
        
        if created:
            print(f"✅ 成功创建测试会话 (ID: {session.id})")
        else:
            print(f"✅ 测试会话已存在 (ID: {session.id})")
        
        # 创建更多测试会话
        for i in range(1000, 1010):
            session, created = DataCollectionSession.objects.get_or_create(
                id=i,
                defaults={
                    'device_group': device_group,
                    'user': wx_user,
                    'status': 'collecting'
                }
            )
            if created:
                print(f"✅ 创建会话 ID: {i}")
        
        # 创建批量测试会话
        batch_session, created = DataCollectionSession.objects.get_or_create(
            id=999,
            defaults={
                'device_group': device_group,
                'user': wx_user,
                'status': 'collecting'
            }
        )
        
        if created:
            print(f"✅ 成功创建批量测试会话 (ID: {batch_session.id})")
        else:
            print(f"✅ 批量测试会话已存在 (ID: {batch_session.id})")
        
        print("\n📊 测试会话创建完成!")
        print("可用的会话ID:")
        sessions = DataCollectionSession.objects.filter(status='collecting').order_by('id')
        for session in sessions:
            print(f"   - 会话ID: {session.id}, 状态: {session.status}")
        
    except Exception as e:
        print(f"❌ 创建测试会话失败: {str(e)}")

if __name__ == "__main__":
    create_test_session() 