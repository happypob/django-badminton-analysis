#!/usr/bin/env python3
"""
测试设备码2025001的数据上传功能
验证STM32 → ESP32 → Django的数据流
"""

import requests
import json
import time
import random
from datetime import datetime

# 服务器配置
SERVER_URL = "http://47.122.129.159:8000"
API_ENDPOINT = f"{SERVER_URL}/wxapp/esp32/upload/"

# 设备配置
DEVICE_CODE = "2025001"  # 新的测试设备码
SESSION_ID = 123

def generate_stm32_sensor_data(sensor_type):
    """模拟STM32发送给ESP32的传感器数据"""
    base_values = {
        "waist": {
            "acc": [1.2, 0.8, 9.8],
            "gyro": [0.1, 0.2, 0.3], 
            "angle": [45.0, 30.0, 60.0]
        },
        "shoulder": {
            "acc": [1.3, 0.9, 9.9],
            "gyro": [0.15, 0.25, 0.35],
            "angle": [50.0, 35.0, 65.0]
        },
        "wrist": {
            "acc": [1.4, 1.0, 10.0],
            "gyro": [0.2, 0.3, 0.4],
            "angle": [55.0, 40.0, 70.0]
        }
    }
    
    base = base_values.get(sensor_type, base_values["waist"])
    
    # 添加随机噪声模拟真实传感器数据
    data = {
        "acc": [base["acc"][i] + random.uniform(-0.1, 0.1) for i in range(3)],
        "gyro": [base["gyro"][i] + random.uniform(-0.05, 0.05) for i in range(3)],
        "angle": [base["angle"][i] + random.uniform(-2.0, 2.0) for i in range(3)]
    }
    
    return data

def simulate_esp32_upload(sensor_type, data):
    """模拟ESP32接收STM32数据并上传到服务器"""
    try:
        # 构建上传数据
        post_data = {
            "device_code": DEVICE_CODE,
            "sensor_type": sensor_type,
            "data": json.dumps(data),
            "session_id": SESSION_ID,
            "timestamp": str(int(time.time()))
        }
        
        print(f"📡 ESP32正在上传 {sensor_type} 传感器数据...")
        print(f"   设备码: {DEVICE_CODE}")
        print(f"   会话ID: {SESSION_ID}")
        print(f"   数据: {json.dumps(data, indent=2)}")
        
        # 发送到Django服务器
        response = requests.post(API_ENDPOINT, data=post_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {sensor_type} 数据上传成功!")
            print(f"   响应: {result}")
            return True
        else:
            print(f"❌ {sensor_type} 数据上传失败!")
            print(f"   状态码: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {sensor_type} 上传异常: {str(e)}")
        return False

def test_single_sensor_upload(sensor_type):
    """测试单个传感器数据上传"""
    print(f"\n🔄 测试 {sensor_type} 传感器数据上传")
    print("=" * 50)
    
    # 模拟STM32生成传感器数据
    sensor_data = generate_stm32_sensor_data(sensor_type)
    
    # 模拟ESP32上传数据
    success = simulate_esp32_upload(sensor_type, sensor_data)
    
    return success

def test_multi_sensor_upload():
    """测试多传感器同时上传"""
    print(f"\n🔄 测试多传感器数据上传 (设备码: {DEVICE_CODE})")
    print("=" * 50)
    
    sensors = ["waist", "shoulder", "wrist"]
    success_count = 0
    
    for sensor_type in sensors:
        if test_single_sensor_upload(sensor_type):
            success_count += 1
        time.sleep(1)  # 间隔1秒
    
    print(f"\n📊 上传结果统计:")
    print(f"   成功: {success_count}/{len(sensors)}")
    print(f"   成功率: {success_count/len(sensors)*100:.1f}%")
    
    return success_count == len(sensors)

def test_continuous_upload(duration=30, interval=2):
    """测试连续数据上传"""
    print(f"\n🔄 测试连续数据上传 ({duration}秒, 间隔{interval}秒)")
    print("=" * 50)
    
    start_time = time.time()
    upload_count = 0
    success_count = 0
    
    while time.time() - start_time < duration:
        # 随机选择一个传感器
        sensor_type = random.choice(["waist", "shoulder", "wrist"])
        
        # 生成并上传数据
        sensor_data = generate_stm32_sensor_data(sensor_type)
        if simulate_esp32_upload(sensor_type, sensor_data):
            success_count += 1
        upload_count += 1
        
        print(f"⏱️  已上传 {upload_count} 条数据, 成功 {success_count} 条")
        time.sleep(interval)
    
    print(f"\n📊 连续上传结果:")
    print(f"   总上传: {upload_count} 条")
    print(f"   成功: {success_count} 条")
    print(f"   成功率: {success_count/upload_count*100:.1f}%")

def check_device_status():
    """检查设备状态"""
    print(f"\n🔍 检查设备 {DEVICE_CODE} 状态")
    print("=" * 50)
    
    try:
        response = requests.post(
            f"{SERVER_URL}/wxapp/esp32/status/",
            data={"device_code": DEVICE_CODE}
        )
        
        if response.status_code == 200:
            status = response.json()
            print(f"✅ 设备状态获取成功:")
            print(f"   设备码: {status.get('device_code')}")
            print(f"   绑定状态: {status.get('is_bound', '未知')}")
            print(f"   最后数据时间: {status.get('last_data_time', '无数据')}")
            print(f"   总数据量: {status.get('total_data_count', 0)} 条")
        else:
            print(f"❌ 设备状态获取失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 设备状态检查异常: {str(e)}")

def main():
    """主测试函数"""
    print("🚀 开始测试设备码 2025001 的数据上传功能")
    print("=" * 60)
    print(f"📱 设备架构: STM32 → ESP32 → Django服务器")
    print(f"🔧 设备码: {DEVICE_CODE}")
    print(f"🌐 服务器: {SERVER_URL}")
    print("=" * 60)
    
    # 1. 检查设备状态
    check_device_status()
    
    # 2. 测试单个传感器上传
    test_single_sensor_upload("waist")
    
    # 3. 测试多传感器上传
    test_multi_sensor_upload()
    
    # 4. 测试连续上传
    test_continuous_upload(duration=10, interval=1)
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    main() 