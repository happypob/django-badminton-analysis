#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地后端测试脚本
"""

import requests
import json
import time

# 本地服务器配置
LOCAL_SERVER_URL = "http://localhost:8000"

def test_local_server():
    """测试本地服务器是否运行"""
    print("🔍 测试本地服务器...")
    
    try:
        response = requests.get(f"{LOCAL_SERVER_URL}/wxapp/test_udp_broadcast/", timeout=5)
        if response.status_code == 200:
            print("✅ 本地服务器运行正常!")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到本地服务器: {str(e)}")
        print("请确保Django服务器正在运行: python manage.py runserver 0.0.0.0:8000")
        return False

def test_udp_broadcast_local():
    """测试本地UDP广播功能"""
    print("\n📡 测试本地UDP广播功能...")
    
    try:
        response = requests.post(
            f"{LOCAL_SERVER_URL}/wxapp/test_udp_broadcast/",
            data={
                'message': 'Hello ESP32 from local test!',
                'device_code': '2025001'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 本地UDP广播测试成功!")
            print(f"   设备码: {result.get('device_code')}")
            print(f"   广播消息: {result.get('broadcast_message')}")
            print(f"   广播端口: {result.get('broadcast_port')}")
            print(f"   结果: {result.get('result')}")
        else:
            print(f"❌ 本地UDP广播测试失败: {response.status_code}")
            print(f"   错误: {response.text}")
            
    except Exception as e:
        print(f"❌ 本地测试失败: {str(e)}")

def test_start_collection_local():
    """测试本地开始采集流程"""
    print("\n🚀 测试本地开始采集流程...")
    
    # 步骤1: 创建会话
    try:
        session_response = requests.post(
            f"{LOCAL_SERVER_URL}/wxapp/start_session/",
            data={
                'openid': 'test_user_123456',
                'device_group_code': '2025001'
            },
            timeout=10
        )
        
        if session_response.status_code == 200:
            session_data = session_response.json()
            session_id = session_data.get('session_id')
            print(f"✅ 本地会话创建成功: {session_id}")
            
            # 步骤2: 开始采集（包含UDP广播）
            start_response = requests.post(
                f"{LOCAL_SERVER_URL}/wxapp/start_data_collection/",
                data={
                    'session_id': session_id,
                    'device_code': '2025001'
                },
                timeout=10
            )
            
            if start_response.status_code == 200:
                result = start_response.json()
                print("✅ 本地开始采集成功（包含UDP广播）!")
                print(f"   会话ID: {result.get('session_id')}")
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
                
                return session_id
            else:
                print(f"❌ 本地开始采集失败: {start_response.status_code}")
                print(f"   错误: {start_response.text}")
        else:
            print(f"❌ 本地会话创建失败: {session_response.status_code}")
            print(f"   错误: {session_response.text}")
            
    except Exception as e:
        print(f"❌ 本地测试失败: {str(e)}")
    
    return None

def test_stop_collection_local(session_id):
    """测试本地停止采集流程"""
    if not session_id:
        print("❌ 没有有效的会话ID，跳过停止采集测试")
        return
    
    print(f"\n🛑 测试本地停止采集流程 (会话ID: {session_id})...")
    
    try:
        end_response = requests.post(
            f"{LOCAL_SERVER_URL}/wxapp/end_session/",
            data={
                'session_id': session_id,
                'device_code': '2025001'
            },
            timeout=10
        )
        
        if end_response.status_code == 200:
            result = end_response.json()
            print("✅ 本地停止采集成功（包含UDP广播）!")
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
        else:
            print(f"❌ 本地停止采集失败: {end_response.status_code}")
            print(f"   错误: {end_response.text}")
            
    except Exception as e:
        print(f"❌ 本地测试失败: {str(e)}")

def test_api_info_local():
    """获取本地API信息"""
    print("\n📋 本地API信息:")
    
    apis = [
        '/wxapp/test_udp_broadcast/',
        '/wxapp/start_session/',
        '/wxapp/start_data_collection/',
        '/wxapp/end_session/'
    ]
    
    for api in apis:
        try:
            response = requests.get(f"{LOCAL_SERVER_URL}{api}", timeout=5)
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
    print("🚀 本地后端测试开始...")
    print(f"   服务器: {LOCAL_SERVER_URL}")
    print("=" * 50)
    
    # 测试服务器连接
    if not test_local_server():
        print("❌ 服务器连接失败，请检查Django是否正在运行")
        exit(1)
    
    # 获取API信息
    test_api_info_local()
    
    # 测试UDP广播
    test_udp_broadcast_local()
    
    # 测试完整流程
    session_id = test_start_collection_local()
    test_stop_collection_local(session_id)
    
    print("\n🎉 本地测试完成!")
    print("\n📝 说明:")
    print("   - 本地服务器: http://localhost:8000")
    print("   - UDP广播端口: 8888")
    print("   - 广播地址: 255.255.255.255")
    print("   - 设备码: 2025001")
    print("\n🔧 下一步:")
    print("   1. 确保ESP32监听UDP端口8888")
    print("   2. 运行ESP32程序测试广播接收")
    print("   3. 检查ESP32串口输出确认消息接收") 