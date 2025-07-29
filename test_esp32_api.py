#!/usr/bin/env python3
"""
ESP32 API 测试脚本
用于测试ESP32-S3与后端的数据传输接口
"""

import requests
import json
import time
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000/wxapp"
ESP32_BASE_URL = "http://localhost:8000/wxapp/esp32"

def test_esp32_upload_single():
    """测试ESP32单条数据上传"""
    print("=== 测试ESP32单条数据上传 ===")
    
    # 模拟ESP32传感器数据
    sensor_data = {
        "acc": [1.2, 0.8, 9.8],
        "gyro": [0.1, 0.2, 0.3],
        "angle": [45.0, 30.0, 60.0]
    }
    
    payload = {
        "device_code": "esp32_001",
        "sensor_type": "waist",
        "data": json.dumps(sensor_data),
        "timestamp": str(int(time.time()))
    }
    
    try:
        response = requests.post(f"{ESP32_BASE_URL}/upload/", data=payload)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def test_esp32_batch_upload():
    """测试ESP32批量数据上传"""
    print("\n=== 测试ESP32批量数据上传 ===")
    
    # 模拟批量传感器数据
    batch_data = []
    for i in range(5):
        data_item = {
            "acc": [1.0 + i*0.1, 0.5 + i*0.05, 9.8],
            "gyro": [0.1 + i*0.01, 0.2 + i*0.02, 0.3 + i*0.03],
            "angle": [40.0 + i*5, 25.0 + i*3, 55.0 + i*2]
        }
        batch_data.append(data_item)
    
    payload = {
        "device_code": "esp32_001",
        "sensor_type": "shoulder",
        "batch_data": json.dumps(batch_data)
    }
    
    try:
        response = requests.post(f"{ESP32_BASE_URL}/batch_upload/", data=payload)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def test_esp32_device_status():
    """测试ESP32设备状态检查"""
    print("\n=== 测试ESP32设备状态检查 ===")
    
    payload = {
        "device_code": "esp32_001"
    }
    
    try:
        response = requests.post(f"{ESP32_BASE_URL}/status/", data=payload)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def test_api_info():
    """测试API信息接口"""
    print("\n=== 测试API信息接口 ===")
    
    try:
        response = requests.get(f"{ESP32_BASE_URL}/upload/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def test_session_management():
    """测试会话管理"""
    print("\n=== 测试会话管理 ===")
    
    # 1. 简化登录
    login_payload = {}
    try:
        login_response = requests.post(f"{BASE_URL}/simple_login/", data=login_payload)
        print(f"登录状态码: {login_response.status_code}")
        login_data = login_response.json()
        print(f"登录响应: {login_data}")
        
        if login_data.get('msg') == 'ok':
            openid = login_data.get('openid')
            
            # 2. 开始会话
            session_payload = {
                "openid": openid,
                "device_group_code": "esp32_group_001"
            }
            
            session_response = requests.post(f"{BASE_URL}/start_session/", data=session_payload)
            print(f"开始会话状态码: {session_response.status_code}")
            session_data = session_response.json()
            print(f"会话响应: {session_data}")
            
            if session_data.get('msg') == 'session started':
                session_id = session_data.get('session_id')
                
                # 3. 上传带会话ID的数据
                sensor_data = {
                    "acc": [1.5, 0.9, 9.8],
                    "gyro": [0.15, 0.25, 0.35],
                    "angle": [50.0, 35.0, 65.0]
                }
                
                upload_payload = {
                    "device_code": "esp32_001",
                    "sensor_type": "wrist",
                    "data": json.dumps(sensor_data),
                    "session_id": session_id,
                    "timestamp": str(int(time.time()))
                }
                
                upload_response = requests.post(f"{ESP32_BASE_URL}/upload/", data=upload_payload)
                print(f"带会话上传状态码: {upload_response.status_code}")
                print(f"上传响应: {upload_response.json()}")
                
                return session_id
                
    except Exception as e:
        print(f"会话管理测试失败: {e}")
        return None

def main():
    """主测试函数"""
    print("ESP32 API 测试开始...")
    print(f"测试时间: {datetime.now()}")
    print("=" * 50)
    
    # 测试API信息
    test_api_info()
    
    # 测试设备状态
    test_esp32_device_status()
    
    # 测试单条数据上传
    test_esp32_upload_single()
    
    # 测试批量数据上传
    test_esp32_batch_upload()
    
    # 测试会话管理
    session_id = test_session_management()
    
    print("\n" + "=" * 50)
    print("ESP32 API 测试完成!")
    
    if session_id:
        print(f"创建的会话ID: {session_id}")
        print(f"可以在管理后台查看会话: http://localhost:8000/admin/")

if __name__ == "__main__":
    main() 