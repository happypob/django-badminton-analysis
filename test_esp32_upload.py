#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32数据上传测试脚本
用于诊断400错误的原因
"""

import requests
import json
import time

# 服务器配置
SERVER_URL = "http://47.122.129.159:8000/wxapp/esp32/upload/"
DEVICE_CODE = "esp32s3_multi_001"
SESSION_ID = 1011

def test_single_upload():
    """测试单个数据上传"""
    print("=== 测试单个数据上传 ===")
    
    # 模拟传感器数据
    sensor_data = {
        "acc": [1.2, 0.8, 9.8],
        "gyro": [0.1, 0.2, 0.3],
        "angle": [45.0, 30.0, 60.0]
    }
    
    # 构建POST数据
    post_data = {
        'device_code': DEVICE_CODE,
        'sensor_type': 'waist',  # 使用正确的传感器类型
        'data': json.dumps(sensor_data),
        'session_id': str(SESSION_ID),
        'timestamp': str(int(time.time() * 1000))
    }
    
    print(f"发送数据: {post_data}")
    
    try:
        response = requests.post(SERVER_URL, data=post_data, timeout=10)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 单个数据上传成功!")
        else:
            print("❌ 单个数据上传失败!")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def test_batch_upload():
    """测试批量数据上传"""
    print("\n=== 测试批量数据上传 ===")
    
    # 模拟批量传感器数据
    batch_data = [
        {
            "acc": [1.2, 0.8, 9.8],
            "gyro": [0.1, 0.2, 0.3],
            "angle": [45.0, 30.0, 60.0]
        },
        {
            "acc": [1.3, 0.9, 9.7],
            "gyro": [0.2, 0.3, 0.4],
            "angle": [46.0, 31.0, 61.0]
        }
    ]
    
    # 构建POST数据
    post_data = {
        'device_code': DEVICE_CODE,
        'sensor_type': 'waist',
        'batch_data': json.dumps(batch_data),  # 使用batch_data参数
        'session_id': str(SESSION_ID),
        'batch_size': str(len(batch_data)),
        'timestamp': str(int(time.time() * 1000))
    }
    
    print(f"发送批量数据: {post_data}")
    
    try:
        response = requests.post(SERVER_URL, data=post_data, timeout=10)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 批量数据上传成功!")
        else:
            print("❌ 批量数据上传失败!")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def test_esp32_original_format():
    """测试ESP32原始格式（可能有问题）"""
    print("\n=== 测试ESP32原始格式 ===")
    
    # 模拟ESP32可能发送的格式
    sensor_data = {
        "acc": [1.2, 0.8, 9.8],
        "gyro": [0.1, 0.2, 0.3],
        "angle": [45.0, 30.0, 60.0]
    }
    
    # 构建POST数据 - 模拟ESP32可能的错误格式
    post_data = {
        'device_code': DEVICE_CODE,
        'sensor_type': 'gyro_1',  # 错误的传感器类型
        'data': json.dumps(sensor_data),
        'session_id': str(SESSION_ID),
        'timestamp': str(int(time.time() * 1000))
    }
    
    print(f"发送数据: {post_data}")
    
    try:
        response = requests.post(SERVER_URL, data=post_data, timeout=10)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ ESP32原始格式上传成功!")
        else:
            print("❌ ESP32原始格式上传失败!")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def test_batch_upload_interface():
    """测试批量上传接口"""
    print("\n=== 测试批量上传接口 ===")
    
    # 使用批量上传专用接口
    batch_url = "http://47.122.129.159:8000/wxapp/esp32/batch_upload/"
    
    # 模拟批量传感器数据
    batch_data = [
        {
            "acc": [1.2, 0.8, 9.8],
            "gyro": [0.1, 0.2, 0.3],
            "angle": [45.0, 30.0, 60.0]
        },
        {
            "acc": [1.3, 0.9, 9.7],
            "gyro": [0.2, 0.3, 0.4],
            "angle": [46.0, 31.0, 61.0]
        }
    ]
    
    # 构建POST数据
    post_data = {
        'device_code': DEVICE_CODE,
        'sensor_type': 'waist',
        'batch_data': json.dumps(batch_data),
        'session_id': str(SESSION_ID)
    }
    
    print(f"发送批量数据到专用接口: {post_data}")
    
    try:
        response = requests.post(batch_url, data=post_data, timeout=10)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 批量上传接口测试成功!")
        else:
            print("❌ 批量上传接口测试失败!")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    print("🚀 ESP32数据上传测试开始")
    print("=" * 50)
    
    # 测试各种格式
    test_single_upload()
    test_batch_upload()
    test_esp32_original_format()
    test_batch_upload_interface()
    
    print("\n" + "=" * 50)
    print("🏁 测试完成") 