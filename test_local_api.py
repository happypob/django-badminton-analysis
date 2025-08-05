#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地API测试脚本
"""

import requests
import json

# 本地服务器配置
LOCAL_SERVER_URL = "http://localhost:8000"

def test_start_session_api():
    """测试开始采集API"""
    print("🔍 测试开始采集API...")
    
    try:
        # 测试GET请求（获取API信息）
        response = requests.get(f"{LOCAL_SERVER_URL}/wxapp/start_session/", timeout=5)
        print(f"GET请求状态码: {response.status_code}")
        print(f"GET响应: {response.text}")
        
        # 测试POST请求（实际开始采集）
        data = {
            'openid': 'test_user_123456',
            'device_group_code': '2025001',
            'device_code': '2025001'
        }
        response = requests.post(f"{LOCAL_SERVER_URL}/wxapp/start_session/", data=data, timeout=10)
        print(f"POST请求状态码: {response.status_code}")
        print(f"POST响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 开始采集成功!")
            print(f"会话ID: {result.get('session_id')}")
            print(f"状态: {result.get('status')}")
            print(f"设备码: {result.get('device_code')}")
            print(f"广播消息: {result.get('broadcast_message')}")
            print(f"广播端口: {result.get('broadcast_port')}")
            return result.get('session_id')
        else:
            print("❌ 开始采集失败")
            return None
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return None

def test_end_session_api(session_id):
    """测试结束采集API"""
    if not session_id:
        print("❌ 没有有效的会话ID，跳过结束采集测试")
        return
    
    print(f"\n🛑 测试结束采集API (会话ID: {session_id})...")
    
    try:
        # 测试GET请求（获取API信息）
        response = requests.get(f"{LOCAL_SERVER_URL}/wxapp/end_session/", timeout=5)
        print(f"GET请求状态码: {response.status_code}")
        print(f"GET响应: {response.text}")
        
        # 测试POST请求（实际结束采集）
        data = {
            'session_id': session_id,
            'device_code': '2025001'
        }
        response = requests.post(f"{LOCAL_SERVER_URL}/wxapp/end_session/", data=data, timeout=10)
        print(f"POST请求状态码: {response.status_code}")
        print(f"POST响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 结束采集成功!")
            print(f"会话ID: {result.get('session_id')}")
            print(f"分析ID: {result.get('analysis_id')}")
            print(f"状态: {result.get('status')}")
            print(f"设备码: {result.get('device_code')}")
            print(f"广播消息: {result.get('broadcast_message')}")
            print(f"广播端口: {result.get('broadcast_port')}")
        else:
            print("❌ 结束采集失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

if __name__ == "__main__":
    print("🚀 本地API测试开始...")
    print(f"服务器: {LOCAL_SERVER_URL}")
    print("=" * 50)
    
    # 测试开始采集
    session_id = test_start_session_api()
    
    # 测试结束采集
    test_end_session_api(session_id)
    
    print("\n🎉 本地测试完成!") 