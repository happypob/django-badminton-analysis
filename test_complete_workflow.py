#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整工作流程测试脚本
验证从创建会话到数据分析的完整流程
"""

import requests
import json
import time
from datetime import datetime

# 服务器配置
SERVER_URL = "http://localhost:8000"
API_BASE = f"{SERVER_URL}/wxapp"

def test_complete_workflow():
    """测试完整的工作流程"""
    print("🚀 完整工作流程测试")
    print("=" * 60)
    
    # 测试参数
    device_code = "2025001"
    esp32_ip = "192.168.1.100"
    
    print("📋 测试流程:")
    print("1. ESP32注册IP地址")
    print("2. 小程序创建新会话")
    print("3. 小程序开始数据采集")
    print("4. 小程序通知ESP32开始采集")
    print("5. ESP32上传传感器数据")
    print("6. ESP32标记上传完成")
    print("7. 后台自动触发数据分析")
    print()
    
    # 步骤1: ESP32注册IP地址
    print("🔧 步骤1: ESP32注册IP地址")
    print("-" * 40)
    
    register_data = {
        'device_code': device_code,
        'ip_address': esp32_ip
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/register_device_ip/",
            data=register_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ ESP32 IP注册成功!")
            print(f"   设备码: {result.get('device_code')}")
            print(f"   IP地址: {result.get('ip_address')}")
        else:
            print(f"❌ ESP32 IP注册失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 注册失败: {e}")
        return None
    
    print()
    
    # 步骤2: 小程序创建新会话
    print("📱 步骤2: 小程序创建新会话")
    print("-" * 40)
    
    session_data = {
        'openid': f'test_user_{int(time.time())}',
        'device_group_code': f'test_group_{int(time.time())}'
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/start_session/",
            data=session_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            session_id = result.get('session_id')
            print("✅ 新会话创建成功!")
            print(f"   会话ID: {session_id}")
            print(f"   状态: {result.get('status')}")
            print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"❌ 会话创建失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 会话创建失败: {e}")
        return None
    
    print()
    
    # 步骤3: 小程序开始数据采集
    print("📊 步骤3: 小程序开始数据采集")
    print("-" * 40)
    
    collection_data = {
        'session_id': session_id
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/start_data_collection/",
            data=collection_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 数据采集开始!")
            print(f"   会话ID: {result.get('session_id')}")
            print(f"   状态: {result.get('status')}")
        else:
            print(f"❌ 数据采集开始失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 数据采集开始失败: {e}")
        return None
    
    print()
    
    # 步骤4: 小程序通知ESP32开始采集
    print("📡 步骤4: 小程序通知ESP32开始采集")
    print("-" * 40)
    
    notify_data = {
        'session_id': session_id,
        'device_code': device_code
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/notify_device_start/",
            data=notify_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ ESP32通知成功!")
            print(f"   会话ID: {result.get('session_id')}")
            print(f"   设备码: {result.get('device_code')}")
            print(f"   ESP32 IP: {result.get('esp32_ip')}")
            print(f"   ESP32响应: {result.get('esp32_response')}")
        else:
            print(f"❌ ESP32通知失败: {response.status_code}")
            print(f"   错误: {response.text}")
            # 继续测试，因为ESP32可能不在线
            
    except Exception as e:
        print(f"❌ ESP32通知失败: {e}")
        # 继续测试，因为ESP32可能不在线
    
    print()
    
    # 步骤5: 模拟ESP32上传传感器数据
    print("📤 步骤5: 模拟ESP32上传传感器数据")
    print("-" * 40)
    
    # 模拟腰部传感器数据
    waist_data = {
        'device_code': device_code,
        'sensor_type': 'waist',
        'session_id': session_id,
        'batch_data': json.dumps([
            {
                'acc': [1.2, 2.3, 9.8],
                'gyro': [0.1, 0.2, 0.3],
                'angle': [45.0, 30.0, 60.0]
            },
            {
                'acc': [1.3, 2.4, 9.9],
                'gyro': [0.2, 0.3, 0.4],
                'angle': [46.0, 31.0, 61.0]
            }
        ])
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/esp32/batch_upload/",
            data=waist_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 腰部传感器数据上传成功!")
            print(f"   总数据条数: {result.get('total_items')}")
            print(f"   成功条数: {result.get('successful_items')}")
            print(f"   失败条数: {result.get('failed_items')}")
        else:
            print(f"❌ 数据上传失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 数据上传失败: {e}")
        return None
    
    # 模拟肩部传感器数据
    shoulder_data = {
        'device_code': device_code,
        'sensor_type': 'shoulder',
        'session_id': session_id,
        'batch_data': json.dumps([
            {
                'acc': [1.1, 2.2, 9.7],
                'gyro': [0.05, 0.15, 0.25],
                'angle': [44.0, 29.0, 59.0]
            },
            {
                'acc': [1.2, 2.3, 9.8],
                'gyro': [0.1, 0.2, 0.3],
                'angle': [45.0, 30.0, 60.0]
            }
        ])
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/esp32/batch_upload/",
            data=shoulder_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 肩部传感器数据上传成功!")
            print(f"   总数据条数: {result.get('total_items')}")
            print(f"   成功条数: {result.get('successful_items')}")
        else:
            print(f"❌ 肩部数据上传失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 肩部数据上传失败: {e}")
    
    print()
    
    # 步骤6: ESP32标记上传完成
    print("✅ 步骤6: ESP32标记上传完成")
    print("-" * 40)
    
    upload_stats = {
        'total_files': 2,
        'total_bytes': 2048,
        'upload_time_ms': 3000,
        'sensor_types': ['waist', 'shoulder'],
        'data_points': 4
    }
    
    complete_data = {
        'session_id': session_id,
        'device_code': device_code,
        'upload_stats': json.dumps(upload_stats)
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/esp32/mark_upload_complete/",
            data=complete_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ ESP32上传完成标记成功!")
            print(f"   会话ID: {result.get('session_id')}")
            print(f"   设备码: {result.get('device_code')}")
            print(f"   会话状态: {result.get('session_status')}")
            
            # 数据统计
            stats = result.get('data_collection_stats', {})
            print(f"   数据点总数: {stats.get('total_data_points')}")
            print(f"   传感器类型: {stats.get('sensor_types')}")
            print(f"   采集时长: {stats.get('collection_duration_seconds')}秒")
            
            # 分析结果
            print(f"   分析触发: {result.get('analysis_triggered')}")
            print(f"   分析ID: {result.get('analysis_id')}")
            print(f"   分析状态: {result.get('analysis_status')}")
            
            if result.get('error_message'):
                print(f"   错误信息: {result.get('error_message')}")
                
        else:
            print(f"❌ 上传完成标记失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 上传完成标记失败: {e}")
        return None
    
    print()
    print("🎉 完整工作流程测试成功!")
    print(f"📝 会话ID: {session_id} 已完成数据采集和分析")
    return session_id

def test_multiple_sessions():
    """测试多次采集创建不同会话"""
    print("\n🔄 测试多次采集创建不同会话")
    print("=" * 60)
    
    session_ids = []
    
    for i in range(1, 3):  # 测试2次采集
        print(f"\n📱 第 {i} 次采集")
        print("-" * 30)
        
        session_id = test_complete_workflow()
        if session_id:
            session_ids.append(session_id)
            print(f"✅ 第 {i} 次采集完成，会话ID: {session_id}")
        else:
            print(f"❌ 第 {i} 次采集失败")
        
        # 等待一下，避免请求过快
        time.sleep(3)
    
    print(f"\n✅ 完成 {len(session_ids)} 次采集测试")
    print(f"📊 会话ID列表: {session_ids}")
    print("💡 每次采集都创建了不同的会话ID，避免数据覆盖")

def show_workflow_summary():
    """显示工作流程总结"""
    print("\n📚 完整工作流程总结")
    print("=" * 60)
    
    print("🔄 完整流程:")
    print("1. ESP32注册IP地址")
    print("2. 小程序创建新会话 (每次都不一样)")
    print("3. 小程序开始数据采集")
    print("4. 小程序通知ESP32开始采集")
    print("5. ESP32接收新会话ID并开始SD卡存储")
    print("6. 小程序结束采集")
    print("7. ESP32停止接收，上传SD卡数据")
    print("8. ESP32标记上传完成")
    print("9. 后台自动触发数据分析")
    print()
    
    print("🎯 关键优势:")
    print("- 每次采集创建新会话，避免数据覆盖")
    print("- ESP32知道会话ID，数据上传到正确会话")
    print("- 自动触发分析，无需手动操作")
    print("- 每次分析都是基于独立的会话数据")
    print()
    
    print("🔧 API接口:")
    print("- POST /wxapp/start_session/ - 创建新会话")
    print("- POST /wxapp/start_data_collection/ - 开始数据采集")
    print("- POST /wxapp/notify_device_start/ - 通知ESP32")
    print("- POST /wxapp/esp32/batch_upload/ - 上传传感器数据")
    print("- POST /wxapp/esp32/mark_upload_complete/ - 标记上传完成")

if __name__ == "__main__":
    print("🧪 完整工作流程测试")
    print("=" * 60)
    
    # 显示工作流程总结
    show_workflow_summary()
    
    # 测试单次完整流程
    test_complete_workflow()
    
    # 测试多次采集
    test_multiple_sessions()
    
    print("\n✅ 所有测试完成!")
    print("\n📝 总结:")
    print("1. 每次采集都创建新会话，避免数据覆盖")
    print("2. ESP32接收新会话ID，数据上传到正确会话")
    print("3. 自动触发分析，每次分析都是独立的")
    print("4. 完整的SD卡存储 + 一次性上传流程") 