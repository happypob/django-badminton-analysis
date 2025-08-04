#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的ESP32数据上传格式
"""

import requests
import json
import time

# 服务器配置
BATCH_URL = "http://47.122.129.159:8000/wxapp/esp32/batch_upload/"
SINGLE_URL = "http://47.122.129.159:8000/wxapp/esp32/upload/"
DEVICE_CODE = "esp32s3_multi_001"
SESSION_ID = 1011

def test_esp32_batch_format():
    """测试ESP32修复后的批量上传格式"""
    print("=== 测试ESP32修复后的批量上传格式 ===")
    
    # 模拟ESP32发送的批量数据格式
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
    
    # 构建POST数据 - 模拟ESP32修复后的格式
    post_data = {
        'device_code': DEVICE_CODE,
        'sensor_type': 'waist',  # 修复：使用正确的传感器类型
        'batch_data': json.dumps(batch_data),  # 修复：使用batch_data参数
        'session_id': str(SESSION_ID)
    }
    
    print(f"发送数据: {post_data}")
    
    try:
        response = requests.post(BATCH_URL, data=post_data, timeout=10)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ ESP32修复后格式测试成功!")
            return True
        else:
            print("❌ ESP32修复后格式测试失败!")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_esp32_single_format():
    """测试ESP32单个数据上传格式"""
    print("\n=== 测试ESP32单个数据上传格式 ===")
    
    # 模拟单个传感器数据
    sensor_data = {
        "acc": [1.2, 0.8, 9.8],
        "gyro": [0.1, 0.2, 0.3],
        "angle": [45.0, 30.0, 60.0]
    }
    
    # 构建POST数据
    post_data = {
        'device_code': DEVICE_CODE,
        'sensor_type': 'waist',  # 修复：使用正确的传感器类型
        'data': json.dumps(sensor_data),  # 单个数据使用data参数
        'session_id': str(SESSION_ID),
        'timestamp': str(int(time.time() * 1000))
    }
    
    print(f"发送数据: {post_data}")
    
    try:
        response = requests.post(SINGLE_URL, data=post_data, timeout=10)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ ESP32单个数据上传测试成功!")
            return True
        else:
            print("❌ ESP32单个数据上传测试失败!")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_multiple_sensors():
    """测试多个传感器的批量上传"""
    print("\n=== 测试多个传感器的批量上传 ===")
    
    # 模拟多个传感器的数据
    sensors_data = {
        'waist': [
            {"acc": [1.2, 0.8, 9.8], "gyro": [0.1, 0.2, 0.3], "angle": [45.0, 30.0, 60.0]},
            {"acc": [1.3, 0.9, 9.7], "gyro": [0.2, 0.3, 0.4], "angle": [46.0, 31.0, 61.0]}
        ],
        'shoulder': [
            {"acc": [1.4, 1.0, 9.6], "gyro": [0.3, 0.4, 0.5], "angle": [47.0, 32.0, 62.0]},
            {"acc": [1.5, 1.1, 9.5], "gyro": [0.4, 0.5, 0.6], "angle": [48.0, 33.0, 63.0]}
        ]
    }
    
    success_count = 0
    total_count = 0
    
    for sensor_type, data_list in sensors_data.items():
        total_count += 1
        
        post_data = {
            'device_code': DEVICE_CODE,
            'sensor_type': sensor_type,
            'batch_data': json.dumps(data_list),
            'session_id': str(SESSION_ID)
        }
        
        print(f"上传 {sensor_type} 传感器: {len(data_list)} 条数据")
        
        try:
            response = requests.post(BATCH_URL, data=post_data, timeout=10)
            if response.status_code == 200:
                print(f"✅ {sensor_type} 传感器上传成功")
                success_count += 1
            else:
                print(f"❌ {sensor_type} 传感器上传失败 (HTTP: {response.status_code})")
                
        except Exception as e:
            print(f"❌ {sensor_type} 传感器上传异常: {e}")
    
    print(f"\n多传感器测试结果: {success_count}/{total_count} 成功")
    return success_count == total_count

if __name__ == "__main__":
    print("🚀 ESP32修复后格式测试开始")
    print("=" * 50)
    
    # 测试各种格式
    test1 = test_esp32_batch_format()
    test2 = test_esp32_single_format()
    test3 = test_multiple_sensors()
    
    print("\n" + "=" * 50)
    print("🏁 测试完成")
    print(f"批量上传测试: {'✅ 通过' if test1 else '❌ 失败'}")
    print(f"单个上传测试: {'✅ 通过' if test2 else '❌ 失败'}")
    print(f"多传感器测试: {'✅ 通过' if test3 else '❌ 失败'}")
    
    if test1 and test2 and test3:
        print("\n🎉 所有测试通过！ESP32代码修复成功！")
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查") 