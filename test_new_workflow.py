#!/usr/bin/env python3
"""
测试新的工作流程：
1. 开始会话 -> calibrating
2. ESP32轮询 -> 收到START_COLLECTION
3. 结束会话 -> stopping
4. ESP32轮询 -> 收到STOP_COLLECTION
5. ESP32上传数据 -> 调用mark_upload_complete
6. 会话状态变为analyzing -> 开始分析
"""

import requests
import json
import time

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

def test_poll_commands(session_id=None, status="idle"):
    """测试轮询接口"""
    print(f"\n🔧 测试轮询接口...")
    
    url = f"{SERVER_URL}/wxapp/esp32/poll_commands/"
    data = {
        'device_code': '2025001',
        'current_session': str(session_id) if session_id else '',
        'status': status
    }
    
    print(f"轮询参数: {data}")
    
    response = requests.post(url, data=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    return response.json() if response.status_code == 200 else None

def test_end_session(session_id):
    """测试结束会话"""
    print(f"\n🔧 测试结束会话...")
    
    url = f"{SERVER_URL}/wxapp/end_session/"
    data = {
        'session_id': session_id
    }
    
    print(f"结束会话参数: {data}")
    
    response = requests.post(url, data=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    return response.json() if response.status_code == 200 else None

def test_mark_upload_complete(session_id):
    """测试标记上传完成"""
    print(f"\n🔧 测试标记上传完成...")
    
    url = f"{SERVER_URL}/wxapp/esp32/mark_upload_complete/"
    data = {
        'session_id': session_id,
        'device_code': '2025001',
        'upload_stats': json.dumps({
            'total_data_points': 100,
            'sensor_types': ['waist', 'shoulder'],
            'collection_duration_seconds': 30,
            'file_size_bytes': 1024,
            'upload_timestamp': int(time.time() * 1000)
        })
    }
    
    print(f"标记上传完成参数: {data}")
    
    response = requests.post(url, data=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    return response.json() if response.status_code == 200 else None

def main():
    """主测试函数"""
    print("🚀 开始测试新的工作流程")
    print("=" * 50)
    
    # 1. 创建会话
    session_id = test_start_session()
    if not session_id:
        print("❌ 会话创建失败")
        return
    
    print(f"✅ 会话创建成功，ID: {session_id}")
    
    # 2. 轮询获取开始指令
    result = test_poll_commands()
    if result and result.get('command') == 'START_COLLECTION':
        print("✅ 轮询成功，收到开始指令")
    else:
        print("❌ 轮询失败或未收到开始指令")
        return
    
    # 3. 结束会话
    result = test_end_session(session_id)
    if result and result.get('status') == 'stopping':
        print("✅ 会话结束成功，状态变为stopping")
    else:
        print("❌ 会话结束失败")
        return
    
    # 4. 轮询获取停止指令
    result = test_poll_commands(session_id, "collecting")
    if result and result.get('command') == 'STOP_COLLECTION':
        print("✅ 轮询成功，收到停止指令")
    else:
        print("❌ 轮询失败或未收到停止指令")
        return
    
    # 5. 标记上传完成
    result = test_mark_upload_complete(session_id)
    if result and result.get('session_status') == 'analyzing':
        print("✅ 标记上传完成成功，状态变为analyzing")
        if result.get('analysis_triggered'):
            print("✅ 数据分析已触发")
        else:
            print("❌ 数据分析触发失败")
    else:
        print("❌ 标记上传完成失败")
        return
    
    print("\n🎉 所有测试通过！新的工作流程正常工作")

if __name__ == "__main__":
    main() 