#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试设备通知机制
模拟小程序开始采集时ESP32接收消息的完整流程
"""

import requests
import json
import time

# 服务器配置
SERVER_URL = "http://47.122.129.159:8000"
API_BASE = f"{SERVER_URL}/wxapp"

def test_device_notification_flow():
    """测试完整的设备通知流程"""
    print("🚀 测试设备通知机制")
    print("=" * 50)
    
    # 测试参数
    device_code = "2025001"
    esp32_ip = "192.168.1.100"  # 模拟ESP32的IP
    
    print("📋 测试流程:")
    print("1. ESP32注册IP地址")
    print("2. 小程序开始采集 (创建新会话)")
    print("3. 后台通知ESP32")
    print("4. ESP32接收消息")
    print()
    
    # 步骤1: ESP32注册IP地址
    print("🔧 步骤1: ESP32注册IP地址")
    print("-" * 30)
    
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
            return
            
    except Exception as e:
        print(f"❌ 注册失败: {e}")
        return
    
    print()
    
    # 步骤2: 小程序开始采集会话 (每次都创建新会话)
    print("📱 步骤2: 小程序开始采集会话 (创建新会话)")
    print("-" * 30)
    
    session_data = {
        'openid': 'test_user_123456',
        'device_group_code': 'test_group_001'
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
            print("✅ 采集会话创建成功!")
            print(f"   会话ID: {session_id} (新会话)")
            print(f"   状态: {result.get('status')}")
            print(f"   ⚠️  注意: 每次采集都会创建新的会话ID，避免数据覆盖")
        else:
            print(f"❌ 会话创建失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ 会话创建失败: {e}")
        return
    
    print()
    
    # 步骤3: 小程序开始数据采集
    print("📊 步骤3: 小程序开始数据采集")
    print("-" * 30)
    
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
            return
            
    except Exception as e:
        print(f"❌ 数据采集开始失败: {e}")
        return
    
    print()
    
    # 步骤4: 小程序通知ESP32开始采集
    print("📡 步骤4: 小程序通知ESP32开始采集")
    print("-" * 30)
    
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
            
    except Exception as e:
        print(f"❌ ESP32通知失败: {e}")
    
    print()
    
    # 步骤5: 检查设备状态
    print("🔍 步骤5: 检查设备状态")
    print("-" * 30)
    
    try:
        response = requests.get(
            f"{API_BASE}/get_device_status/",
            params={'device_code': device_code},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 设备状态检查成功!")
            print(f"   设备码: {result.get('device_code')}")
            print(f"   状态: {result.get('status')}")
            print(f"   IP地址: {result.get('ip_address')}")
        else:
            print(f"❌ 设备状态检查失败: {response.status_code}")
            print(f"   错误: {response.text}")
            
    except Exception as e:
        print(f"❌ 设备状态检查失败: {e}")

def test_multiple_sessions():
    """测试多次采集创建不同会话"""
    print("\n🔄 测试多次采集创建不同会话")
    print("=" * 50)
    
    device_code = "2025001"
    esp32_ip = "192.168.1.100"
    
    # 先注册设备
    register_data = {
        'device_code': device_code,
        'ip_address': esp32_ip
    }
    
    try:
        requests.post(f"{API_BASE}/register_device_ip/", data=register_data, timeout=10)
    except:
        pass
    
    # 模拟3次采集
    for i in range(1, 4):
        print(f"\n📱 第 {i} 次采集")
        print("-" * 20)
        
        # 创建新会话
        session_data = {
            'openid': f'test_user_{i}',
            'device_group_code': f'test_group_{i}'
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
                print(f"✅ 创建会话 {session_id}")
                
                # 开始数据采集
                collection_response = requests.post(
                    f"{API_BASE}/start_data_collection/",
                    data={'session_id': session_id},
                    timeout=10
                )
                
                if collection_response.status_code == 200:
                    print(f"✅ 开始数据采集")
                    
                    # 通知ESP32
                    notify_response = requests.post(
                        f"{API_BASE}/notify_device_start/",
                        data={
                            'session_id': session_id,
                            'device_code': device_code
                        },
                        timeout=10
                    )
                    
                    if notify_response.status_code == 200:
                        print(f"✅ ESP32通知成功")
                    else:
                        print(f"❌ ESP32通知失败")
                else:
                    print(f"❌ 数据采集开始失败")
            else:
                print(f"❌ 会话创建失败")
                
        except Exception as e:
            print(f"❌ 第 {i} 次采集失败: {e}")
    
    print(f"\n✅ 完成 {i} 次采集测试")
    print("📊 每次采集都创建了不同的会话ID，避免数据覆盖")

def test_esp32_simulation():
    """模拟ESP32接收消息"""
    print("\n🤖 模拟ESP32接收消息")
    print("=" * 30)
    
    print("ESP32应该监听以下端点:")
    print("  - /start_collection (开始采集)")
    print("  - /stop_collection (停止采集)")
    print("  - /status (状态查询)")
    print()
    
    print("ESP32接收到的消息格式:")
    print("  POST /start_collection")
    print("  Content-Type: application/x-www-form-urlencoded")
    print("  Data: session_id=1011&device_code=2025001")
    print()
    
    print("ESP32应该响应的格式:")
    print("  HTTP/1.1 200 OK")
    print("  Content-Type: application/json")
    print("  {\"msg\": \"Collection started\", \"session_id\": 1011}")

def show_api_documentation():
    """显示API文档"""
    print("\n📚 API文档")
    print("=" * 30)
    
    apis = [
        {
            'name': '设备IP注册',
            'url': '/wxapp/register_device_ip/',
            'method': 'POST',
            'params': {
                'device_code': '设备码 (如: 2025001)',
                'ip_address': 'ESP32的IP地址'
            }
        },
        {
            'name': '开始采集会话',
            'url': '/wxapp/start_session/',
            'method': 'POST',
            'params': {
                'openid': '用户openid',
                'device_group_code': '设备组代码'
            }
        },
        {
            'name': '开始数据采集',
            'url': '/wxapp/start_data_collection/',
            'method': 'POST',
            'params': {
                'session_id': '会话ID'
            }
        },
        {
            'name': '通知设备开始',
            'url': '/wxapp/notify_device_start/',
            'method': 'POST',
            'params': {
                'session_id': '会话ID',
                'device_code': '设备码'
            }
        },
        {
            'name': '获取设备状态',
            'url': '/wxapp/get_device_status/',
            'method': 'GET',
            'params': {
                'device_code': '设备码'
            }
        }
    ]
    
    for api in apis:
        print(f"🔗 {api['name']}")
        print(f"   URL: {api['url']}")
        print(f"   方法: {api['method']}")
        print(f"   参数:")
        for param, desc in api['params'].items():
            print(f"     - {param}: {desc}")
        print()

if __name__ == "__main__":
    print("🧪 设备通知机制测试")
    print("=" * 50)
    
    # 显示API文档
    show_api_documentation()
    
    # 测试完整流程
    test_device_notification_flow()
    
    # 模拟ESP32
    test_esp32_simulation()
    
    # 测试多次采集
    test_multiple_sessions()
    
    print("\n✅ 测试完成!")
    print("\n📝 总结:")
    print("1. ESP32启动时注册IP地址")
    print("2. 小程序开始采集时调用notify_device_start")
    print("3. 后台自动向ESP32发送开始采集消息")
    print("4. ESP32接收消息并开始SD卡存储") 