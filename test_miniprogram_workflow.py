#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小程序完整工作流程测试脚本
模拟小程序点击开始采集的完整流程
"""

import requests
import json
import time

# 服务器配置
SERVER_URL = "http://47.122.129.159:8000"

def test_miniprogram_start_collection():
    """测试小程序开始采集的完整流程"""
    print("🚀 小程序开始采集流程测试...")
    print("=" * 50)
    
    # 步骤1: 创建会话
    print("📝 步骤1: 创建数据采集会话")
    try:
        session_response = requests.post(
            f"{SERVER_URL}/wxapp/start_session/",
            data={
                'openid': 'test_user_123456',
                'device_code': '2025001'
            },
            timeout=10
        )
        
        if session_response.status_code == 200:
            session_data = session_response.json()
            session_id = session_data.get('session_id')
            status = session_data.get('status')
            print(f"✅ 会话创建成功!")
            print(f"   会话ID: {session_id}")
            print(f"   状态: {status}")
            print(f"   校准命令: {session_data.get('calibration_command')}")
        else:
            print(f"❌ 会话创建失败: {session_response.status_code}")
            print(f"   错误: {session_response.text}")
            return
    except Exception as e:
        print(f"❌ 会话创建异常: {str(e)}")
        return
    
    print()
    
    # 步骤2: 开始数据采集（包含UDP广播）
    print("📡 步骤2: 开始数据采集并发送UDP广播")
    try:
        start_response = requests.post(
            f"{SERVER_URL}/wxapp/start_data_collection/",
            data={
                'session_id': session_id,
                'device_code': '2025001'
            },
            timeout=10
        )
        
        if start_response.status_code == 200:
            result = start_response.json()
            print(f"✅ 数据采集开始成功!")
            print(f"   会话ID: {result.get('session_id')}")
            print(f"   状态: {result.get('status')}")
            print(f"   设备码: {result.get('device_code')}")
            print(f"   广播消息: {result.get('broadcast_message')}")
            print(f"   广播端口: {result.get('broadcast_port')}")
            print(f"   时间戳: {result.get('timestamp')}")
            
            # 解析广播消息
            broadcast_msg = json.loads(result.get('broadcast_message', '{}'))
            print(f"   解析的广播消息:")
            print(f"     - 命令: {broadcast_msg.get('command')}")
            print(f"     - 会话ID: {broadcast_msg.get('session_id')}")
            print(f"     - 设备码: {broadcast_msg.get('device_code')}")
            print(f"     - 时间戳: {broadcast_msg.get('timestamp')}")
            
        else:
            print(f"❌ 数据采集开始失败: {start_response.status_code}")
            print(f"   错误: {start_response.text}")
            return
    except Exception as e:
        print(f"❌ 数据采集开始异常: {str(e)}")
        return
    
    print()
    
    # 步骤3: 模拟数据上传（ESP32上传数据）
    print("📊 步骤3: 模拟ESP32上传传感器数据")
    try:
        # 模拟上传一些测试数据
        for i in range(3):
            upload_response = requests.post(
                f"{SERVER_URL}/wxapp/esp32/upload/",
                data={
                    'device_code': '2025001',
                    'session_id': session_id,
                    'sensor_type': 'waist',
                    'data': json.dumps({
                        'acc': [1.2 + i*0.1, 2.3 + i*0.1, 3.4 + i*0.1],
                        'gyro': [4.5 + i*0.1, 5.6 + i*0.1, 6.7 + i*0.1],
                        'angle': [10.1 + i, 20.2 + i, 30.3 + i]
                    })
                },
                timeout=10
            )
            
            if upload_response.status_code == 200:
                upload_result = upload_response.json()
                print(f"✅ 数据上传 {i+1}/3 成功!")
                print(f"   数据ID: {upload_result.get('data_id')}")
            else:
                print(f"❌ 数据上传 {i+1}/3 失败: {upload_response.status_code}")
            
            time.sleep(1)  # 模拟数据采集间隔
    except Exception as e:
        print(f"❌ 数据上传异常: {str(e)}")
    
    print()
    
    # 步骤4: 结束会话（包含停止采集广播）
    print("🛑 步骤4: 结束会话并发送停止采集广播")
    try:
        end_response = requests.post(
            f"{SERVER_URL}/wxapp/end_session/",
            data={
                'session_id': session_id,
                'device_code': '2025001'
            },
            timeout=10
        )
        
        if end_response.status_code == 200:
            result = end_response.json()
            print(f"✅ 会话结束成功（包含UDP广播）!")
            print(f"   会话ID: {result.get('session_id')}")
            print(f"   分析ID: {result.get('analysis_id')}")
            print(f"   状态: {result.get('status')}")
            print(f"   设备码: {result.get('device_code')}")
            print(f"   广播消息: {result.get('broadcast_message')}")
            print(f"   广播端口: {result.get('broadcast_port')}")
            
            # 解析广播消息
            broadcast_msg = json.loads(result.get('broadcast_message', '{}'))
            print(f"   解析的广播消息:")
            print(f"     - 命令: {broadcast_msg.get('command')}")
            print(f"     - 会话ID: {broadcast_msg.get('session_id')}")
            print(f"     - 设备码: {broadcast_msg.get('device_code')}")
            print(f"     - 时间戳: {broadcast_msg.get('timestamp')}")
        else:
            print(f"❌ 会话结束失败: {end_response.status_code}")
            print(f"   错误: {end_response.text}")
    except Exception as e:
        print(f"❌ 会话结束异常: {str(e)}")
    
    print()
    print("🎉 小程序完整工作流程测试完成!")
    print("\n📝 流程总结:")
    print("   1. 创建会话 (start_session)")
    print("   2. 开始采集 (start_data_collection) - 包含UDP广播")
    print("   3. ESP32上传数据 (esp32/upload)")
    print("   4. 结束会话 (end_session) - 包含停止采集UDP广播")

def test_api_info():
    """获取相关API信息"""
    print("\n📋 相关API信息:")
    
    apis = [
        '/wxapp/start_session/',
        '/wxapp/start_data_collection/',
        '/wxapp/esp32/upload/',
        '/wxapp/end_session/'
    ]
    
    for api in apis:
        try:
            response = requests.get(f"{SERVER_URL}{api}", timeout=5)
            if response.status_code == 200:
                info = response.json()
                print(f"✅ {api}")
                print(f"   描述: {info.get('msg', 'N/A')}")
                if 'required_params' in info:
                    print(f"   必需参数: {info.get('required_params')}")
                if 'optional_params' in info:
                    print(f"   可选参数: {info.get('optional_params')}")
            else:
                print(f"❌ {api}: {response.status_code}")
        except Exception as e:
            print(f"❌ {api}: {str(e)}")
        print()

if __name__ == "__main__":
    print("🚀 小程序完整工作流程测试")
    print(f"   服务器: {SERVER_URL}")
    print("=" * 50)
    
    # 获取API信息
    test_api_info()
    
    # 测试完整流程
    test_miniprogram_start_collection() 