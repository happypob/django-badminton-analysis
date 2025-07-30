#!/usr/bin/env python3
"""
多传感器数据上传测试脚本
用于测试ESP32同时上传多个传感器数据的功能
"""

import requests
import json
import time
import random
from datetime import datetime

# 服务器配置
# SERVER_URL = "http://localhost:8000"  # 本地测试
SERVER_URL = "http://47.122.129.159:8000"  # 远程服务器
API_ENDPOINT = f"{SERVER_URL}/wxapp/esp32/upload/"

# 传感器配置
SENSORS = [
    {
        "device_code": "esp32_waist_001",
        "sensor_type": "waist",
        "name": "腰部传感器"
    },
    {
        "device_code": "esp32_shoulder_001", 
        "sensor_type": "shoulder",
        "name": "肩部传感器"
    },
    {
        "device_code": "esp32_wrist_001",
        "sensor_type": "wrist", 
        "name": "腕部传感器"
    }
]

def generate_sensor_data(sensor_type, base_values=None):
    """生成模拟传感器数据"""
    if base_values is None:
        base_values = {
            "waist": {"acc": [1.2, 0.8, 9.8], "gyro": [0.1, 0.2, 0.3], "angle": [45.0, 30.0, 60.0]},
            "shoulder": {"acc": [1.3, 0.9, 9.9], "gyro": [0.15, 0.25, 0.35], "angle": [50.0, 35.0, 65.0]},
            "wrist": {"acc": [1.4, 1.0, 10.0], "gyro": [0.2, 0.3, 0.4], "angle": [55.0, 40.0, 70.0]}
        }
    
    base = base_values.get(sensor_type, base_values["waist"])
    
    # 添加随机噪声
    data = {
        "acc": [base["acc"][i] + random.uniform(-0.1, 0.1) for i in range(3)],
        "gyro": [base["gyro"][i] + random.uniform(-0.05, 0.05) for i in range(3)],
        "angle": [base["angle"][i] + random.uniform(-2.0, 2.0) for i in range(3)]
    }
    
    return data

def upload_single_sensor_data(sensor_config, session_id=123):
    """上传单个传感器数据"""
    try:
        # 生成传感器数据
        sensor_data = generate_sensor_data(sensor_config["sensor_type"])
        
        # 构建请求数据
        post_data = {
            "device_code": sensor_config["device_code"],
            "sensor_type": sensor_config["sensor_type"],
            "data": json.dumps(sensor_data),
            "session_id": session_id,
            "timestamp": str(int(time.time()))
        }
        
        # 发送请求
        response = requests.post(API_ENDPOINT, data=post_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {sensor_config['name']} 上传成功:")
            print(f"   - 数据ID: {result.get('data_id')}")
            print(f"   - 加速度幅值: {result.get('sensor_data_summary', {}).get('acc_magnitude')}")
            print(f"   - 角速度幅值: {result.get('sensor_data_summary', {}).get('gyro_magnitude')}")
            return True
        else:
            print(f"❌ {sensor_config['name']} 上传失败:")
            print(f"   - 状态码: {response.status_code}")
            print(f"   - 错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {sensor_config['name']} 上传异常: {str(e)}")
        return False

def upload_all_sensors_data(session_id=123):
    """同时上传所有传感器数据"""
    print(f"\n🔄 开始上传多传感器数据 (会话ID: {session_id})")
    print("=" * 50)
    
    success_count = 0
    total_count = len(SENSORS)
    
    for sensor in SENSORS:
        print(f"\n📡 上传 {sensor['name']} 数据...")
        if upload_single_sensor_data(sensor, session_id):
            success_count += 1
        time.sleep(0.1)  # 短暂延迟
    
    print("\n" + "=" * 50)
    print(f"📊 上传结果统计:")
    print(f"   - 成功: {success_count}/{total_count}")
    print(f"   - 失败: {total_count - success_count}/{total_count}")
    print(f"   - 成功率: {success_count/total_count*100:.1f}%")
    
    return success_count == total_count

def test_continuous_upload(duration=30, interval=1):
    """测试连续上传"""
    print(f"\n🔄 开始连续上传测试 (持续时间: {duration}秒, 间隔: {interval}秒)")
    print("=" * 50)
    
    start_time = time.time()
    cycle = 0
    
    while time.time() - start_time < duration:
        cycle += 1
        print(f"\n🔄 第 {cycle} 轮上传 ({time.time() - start_time:.1f}s)")
        
        success = upload_all_sensors_data(1000 + cycle)
        
        if success:
            print("✅ 本轮所有传感器上传成功")
        else:
            print("⚠️ 本轮部分传感器上传失败")
        
        time.sleep(interval)
    
    print(f"\n✅ 连续上传测试完成，共执行 {cycle} 轮")

def test_batch_upload():
    """测试批量上传"""
    print(f"\n🔄 测试批量上传功能")
    print("=" * 50)
    
    batch_url = f"{SERVER_URL}/wxapp/esp32/batch_upload/"
    
    # 生成批量数据
    batch_data = []
    for sensor in SENSORS:
        for i in range(3):  # 每个传感器3个样本
            sensor_data = generate_sensor_data(sensor["sensor_type"])
            batch_data.append(sensor_data)
    
    try:
        post_data = {
            "device_code": "esp32_multi_001",
            "sensor_type": "waist",  # 批量上传时使用一个类型
            "batch_data": json.dumps(batch_data),
            "session_id": "999"
        }
        
        response = requests.post(batch_url, data=post_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 批量上传成功:")
            print(f"   - 总数据条数: {result.get('total_items')}")
            print(f"   - 成功条数: {result.get('successful_items')}")
            print(f"   - 失败条数: {result.get('failed_items')}")
        else:
            print(f"❌ 批量上传失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 批量上传异常: {str(e)}")

def main():
    """主函数"""
    print("🚀 多传感器数据上传测试")
    print("=" * 50)
    
    # 测试1: 单次多传感器上传
    print("\n📋 测试1: 单次多传感器上传")
    upload_all_sensors_data(123)
    
    # 测试2: 连续上传测试
    print("\n📋 测试2: 连续上传测试 (10秒)")
    test_continuous_upload(duration=10, interval=2)
    
    # 测试3: 批量上传测试
    print("\n📋 测试3: 批量上传测试")
    test_batch_upload()
    
    print("\n✅ 所有测试完成!")

if __name__ == "__main__":
    main() 