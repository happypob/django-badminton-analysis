#!/usr/bin/env python3
"""
轮询调试脚本
用于测试ESP32轮询接口的会话查找逻辑
"""

import requests
import json

# 服务器配置
SERVER_URL = "http://localhost:8000"

def test_start_session():
    """测试创建会话"""
    print("🔧 测试创建会话...")
    
    url = f"{SERVER_URL}/wxapp/start_session/"
    data = {
        'openid': 'test_user_123456',
        'device_group_code': '2025001',
        'device_code': '2025001'
    }
    
    response = requests.post(url, data=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        return result.get('session_id')
    return None

def test_poll_commands(session_id=None):
    """测试轮询接口"""
    print(f"\n🔧 测试轮询接口...")
    
    url = f"{SERVER_URL}/wxapp/esp32/poll_commands/"
    data = {
        'device_code': '2025001',
        'current_session': str(session_id) if session_id else '',
        'status': 'idle'
    }
    
    print(f"轮询参数: {data}")
    
    response = requests.post(url, data=data)
    print(f"状态码: {response.status_code}")
    print(f"响应长度: {len(response.text)} 字节")
    print(f"响应内容: {response.text}")
    
    return response.json() if response.status_code == 200 else None

def test_database_query():
    """测试数据库查询逻辑"""
    print(f"\n🔧 测试数据库查询逻辑...")
    
    # 这里需要导入Django模型
    import os
    import django
    
    # 设置Django环境
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangodemo.settings')
    django.setup()
    
    from wxapp.models import DataCollectionSession, DeviceGroup
    
    # 查找设备组
    device_group = DeviceGroup.objects.filter(group_code='2025001').first()
    print(f"设备组: {device_group}")
    
    if device_group:
        # 查找最新会话
        latest_session = DataCollectionSession.objects.filter(
            device_group=device_group
        ).order_by('-start_time').first()
        
        print(f"最新会话: {latest_session}")
        if latest_session:
            print(f"  会话ID: {latest_session.id}")
            print(f"  状态: {latest_session.status}")
            print(f"  设备组: {latest_session.device_group.group_code}")
    else:
        print("❌ 未找到设备组 '2025001'")

def main():
    """主测试函数"""
    print("🚀 开始轮询调试测试")
    print("=" * 50)
    
    # 1. 测试数据库查询
    test_database_query()
    
    # 2. 测试创建会话
    session_id = test_start_session()
    
    if session_id:
        print(f"\n✅ 会话创建成功，ID: {session_id}")
        
        # 3. 测试轮询（应该收到开始指令）
        result = test_poll_commands()
        
        if result and result.get('command') == 'START_COLLECTION':
            print("✅ 轮询成功，收到开始指令")
            
            # 4. 再次轮询（应该收到null）
            result2 = test_poll_commands(session_id)
            print(f"第二次轮询结果: {result2}")
        else:
            print("❌ 轮询失败或未收到开始指令")
    else:
        print("❌ 会话创建失败")

if __name__ == "__main__":
    main() 