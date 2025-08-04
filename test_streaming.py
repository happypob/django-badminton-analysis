#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ESP32流式传输功能
"""

import requests
import json
import time
import threading

# 服务器配置
STREAMING_URL = "http://47.122.129.159:8000/wxapp/esp32/upload/"
DEVICE_CODE = "esp32s3_multi_001"
SESSION_ID = 1011

def test_streaming_single_data():
    """测试单个数据流式传输"""
    print("=== 测试单个数据流式传输 ===")
    
    # 模拟传感器数据
    sensor_data = {
        "acc": [1.2, 0.8, 9.8],
        "gyro": [0.1, 0.2, 0.3],
        "angle": [45.0, 30.0, 60.0]
    }
    
    # 构建POST数据 - 流式传输格式
    post_data = {
        'device_code': DEVICE_CODE,
        'sensor_type': 'waist',
        'data': json.dumps(sensor_data),
        'session_id': str(SESSION_ID),
        'timestamp': str(int(time.time() * 1000)),
        'streaming': 'true'  # 标记为流式传输
    }
    
    print(f"发送流式数据: {post_data}")
    
    try:
        response = requests.post(STREAMING_URL, data=post_data, timeout=10)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 单个数据流式传输测试成功!")
            return True
        else:
            print("❌ 单个数据流式传输测试失败!")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def simulate_streaming_data():
    """模拟流式数据传输"""
    print("\n=== 模拟流式数据传输 ===")
    
    sensors = ['waist', 'shoulder', 'wrist', 'racket']
    success_count = 0
    total_count = 0
    
    for i in range(10):  # 模拟10次流式传输
        for sensor_type in sensors:
            total_count += 1
            
            # 模拟实时传感器数据
            sensor_data = {
                "acc": [1.2 + i*0.1, 0.8 + i*0.05, 9.8],
                "gyro": [0.1 + i*0.01, 0.2 + i*0.01, 0.3 + i*0.01],
                "angle": [45.0 + i, 30.0 + i*0.5, 60.0 + i*0.5]
            }
            
            post_data = {
                'device_code': DEVICE_CODE,
                'sensor_type': sensor_type,
                'data': json.dumps(sensor_data),
                'session_id': str(SESSION_ID),
                'timestamp': str(int(time.time() * 1000)),
                'streaming': 'true'
            }
            
            print(f"流式传输 {sensor_type} 传感器数据 #{i+1}")
            
            try:
                response = requests.post(STREAMING_URL, data=post_data, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {sensor_type} 流式传输成功")
                    success_count += 1
                else:
                    print(f"❌ {sensor_type} 流式传输失败 (HTTP: {response.status_code})")
                    
            except Exception as e:
                print(f"❌ {sensor_type} 流式传输异常: {e}")
            
            # 模拟100ms的流式传输间隔
            time.sleep(0.1)
    
    print(f"\n流式传输测试结果: {success_count}/{total_count} 成功")
    return success_count == total_count

def test_high_frequency_streaming():
    """测试高频流式传输"""
    print("\n=== 测试高频流式传输 ===")
    
    success_count = 0
    total_count = 0
    
    # 模拟高频数据流（每50ms一次）
    for i in range(20):  # 20次高频传输
        total_count += 1
        
        sensor_data = {
            "acc": [1.2 + i*0.05, 0.8 + i*0.02, 9.8],
            "gyro": [0.1 + i*0.005, 0.2 + i*0.005, 0.3 + i*0.005],
            "angle": [45.0 + i*0.5, 30.0 + i*0.25, 60.0 + i*0.25]
        }
        
        post_data = {
            'device_code': DEVICE_CODE,
            'sensor_type': 'waist',  # 只测试腰部传感器
            'data': json.dumps(sensor_data),
            'session_id': str(SESSION_ID),
            'timestamp': str(int(time.time() * 1000)),
            'streaming': 'true'
        }
        
        try:
            response = requests.post(STREAMING_URL, data=post_data, timeout=3)
            if response.status_code == 200:
                print(f"✅ 高频传输 #{i+1} 成功")
                success_count += 1
            else:
                print(f"❌ 高频传输 #{i+1} 失败 (HTTP: {response.status_code})")
                
        except Exception as e:
            print(f"❌ 高频传输 #{i+1} 异常: {e}")
        
        # 50ms间隔
        time.sleep(0.05)
    
    print(f"\n高频流式传输测试结果: {success_count}/{total_count} 成功")
    return success_count == total_count

def test_multi_sensor_streaming():
    """测试多传感器并发流式传输"""
    print("\n=== 测试多传感器并发流式传输 ===")
    
    def stream_sensor_data(sensor_type, data_count):
        """单个传感器的流式传输函数"""
        success_count = 0
        for i in range(data_count):
            sensor_data = {
                "acc": [1.2 + i*0.1, 0.8 + i*0.05, 9.8],
                "gyro": [0.1 + i*0.01, 0.2 + i*0.01, 0.3 + i*0.01],
                "angle": [45.0 + i, 30.0 + i*0.5, 60.0 + i*0.5]
            }
            
            post_data = {
                'device_code': DEVICE_CODE,
                'sensor_type': sensor_type,
                'data': json.dumps(sensor_data),
                'session_id': str(SESSION_ID),
                'timestamp': str(int(time.time() * 1000)),
                'streaming': 'true'
            }
            
            try:
                response = requests.post(STREAMING_URL, data=post_data, timeout=5)
                if response.status_code == 200:
                    success_count += 1
                    
            except Exception as e:
                print(f"❌ {sensor_type} 流式传输异常: {e}")
            
            time.sleep(0.1)  # 100ms间隔
        
        return success_count
    
    # 创建多个线程模拟并发流式传输
    sensors = ['waist', 'shoulder', 'wrist', 'racket']
    threads = []
    results = {}
    
    for sensor_type in sensors:
        thread = threading.Thread(
            target=lambda s=sensor_type: results.update({s: stream_sensor_data(s, 5)})
        )
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    # 统计结果
    total_success = sum(results.values())
    total_count = len(sensors) * 5
    
    print(f"多传感器并发流式传输结果:")
    for sensor_type, success_count in results.items():
        print(f"  {sensor_type}: {success_count}/5 成功")
    
    print(f"总计: {total_success}/{total_count} 成功")
    return total_success == total_count

if __name__ == "__main__":
    print("🚀 ESP32流式传输测试开始")
    print("=" * 50)
    
    # 测试各种流式传输场景
    test1 = test_streaming_single_data()
    test2 = simulate_streaming_data()
    test3 = test_high_frequency_streaming()
    test4 = test_multi_sensor_streaming()
    
    print("\n" + "=" * 50)
    print("🏁 流式传输测试完成")
    print(f"单个数据流式传输: {'✅ 通过' if test1 else '❌ 失败'}")
    print(f"模拟流式数据传输: {'✅ 通过' if test2 else '❌ 失败'}")
    print(f"高频流式传输: {'✅ 通过' if test3 else '❌ 失败'}")
    print(f"多传感器并发流式传输: {'✅ 通过' if test4 else '❌ 失败'}")
    
    if test1 and test2 and test3 and test4:
        print("\n🎉 所有流式传输测试通过！ESP32流式传输功能正常！")
    else:
        print("\n⚠️ 部分流式传输测试失败，需要进一步检查") 