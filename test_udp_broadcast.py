#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UDP广播功能测试脚本
"""

import requests
import json

# 服务器配置
SERVER_URL = "http://47.122.129.159:8000"

def test_udp_broadcast():
    """测试UDP广播功能"""
    print("🧪 测试UDP广播功能...")
    
    # 测试UDP广播
    try:
        response = requests.post(
            f"{SERVER_URL}/wxapp/test_udp_broadcast/",
            data={
                'message': 'Hello ESP32 from test script!',
                'device_code': '2025001'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ UDP广播测试成功!")
            print(f"   设备码: {result.get('device_code')}")
            print(f"   消息: {result.get('broadcast_message')}")
            print(f"   端口: {result.get('broadcast_port')}")
            print(f"   结果: {result.get('result')}")
        else:
            print(f"❌ UDP广播测试失败: {response.status_code}")
            print(f"   错误: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def test_start_collection_broadcast():
    """测试开始采集广播"""
    print("\n📡 测试开始采集广播...")
    
    # 首先创建一个测试会话
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
            print(f"✅ 创建测试会话成功: {session_id}")
            
            # 使用新的start_data_collection接口（包含广播）
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
                print("✅ 开始采集成功（包含UDP广播）!")
                print(f"   会话ID: {result.get('session_id')}")
                print(f"   状态: {result.get('status')}")
                print(f"   设备码: {result.get('device_code')}")
                print(f"   广播消息: {result.get('broadcast_message')}")
                print(f"   广播端口: {result.get('broadcast_port')}")
            else:
                print(f"❌ 开始采集失败: {start_response.status_code}")
                print(f"   错误: {start_response.text}")
        else:
            print(f"❌ 创建会话失败: {session_response.status_code}")
            print(f"   错误: {session_response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def test_stop_collection_broadcast():
    """测试停止采集广播"""
    print("\n🛑 测试停止采集广播...")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/wxapp/notify_esp32_stop/",
            data={'device_code': '2025001'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 停止采集广播发送成功!")
            print(f"   设备码: {result.get('device_code')}")
            print(f"   广播消息: {result.get('broadcast_message')}")
            print(f"   广播端口: {result.get('broadcast_port')}")
        else:
            print(f"❌ 停止采集广播失败: {response.status_code}")
            print(f"   错误: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def get_api_info():
    """获取API信息"""
    print("\n📋 获取API信息...")
    
    apis = [
        '/wxapp/test_udp_broadcast/',
        '/wxapp/notify_esp32_start/',
        '/wxapp/notify_esp32_stop/'
    ]
    
    for api in apis:
        try:
            response = requests.get(f"{SERVER_URL}{api}", timeout=5)
            if response.status_code == 200:
                info = response.json()
                print(f"✅ {api}")
                print(f"   描述: {info.get('msg')}")
                if 'broadcast_config' in info:
                    config = info['broadcast_config']
                    print(f"   广播端口: {config.get('port')}")
                    print(f"   广播地址: {config.get('address')}")
            else:
                print(f"❌ {api}: {response.status_code}")
        except Exception as e:
            print(f"❌ {api}: {str(e)}")
        print()

if __name__ == "__main__":
    print("🚀 UDP广播功能测试开始...")
    print(f"   服务器: {SERVER_URL}")
    print("=" * 50)
    
    # 获取API信息
    get_api_info()
    
    # 测试UDP广播
    test_udp_broadcast()
    
    # 测试开始采集广播
    test_start_collection_broadcast()
    
    # 测试停止采集广播
    test_stop_collection_broadcast()
    
    print("\n🎉 测试完成!")
    print("\n📝 说明:")
    print("   - ESP32需要监听UDP端口8888")
    print("   - 广播地址: 255.255.255.255")
    print("   - 消息格式: JSON字符串")
    print("   - 命令类型: START_COLLECTION, STOP_COLLECTION, TEST")
    print("   - 设备码: 2025001 (默认)") 