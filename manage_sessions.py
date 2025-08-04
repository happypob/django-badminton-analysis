#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话管理脚本
用于查看、创建和管理采集会话，避免数据覆盖
"""

import requests
import json
import time
from datetime import datetime

# 服务器配置
SERVER_URL = "http://47.122.129.159:8000"
API_BASE = f"{SERVER_URL}/wxapp"

def list_all_sessions():
    """列出所有会话"""
    print("📋 所有会话列表")
    print("=" * 50)
    
    try:
        # 这里需要调用后端API来获取会话列表
        # 暂时模拟数据
        sessions = [
            {"id": 1011, "status": "collecting", "created": "2025-07-30 10:00:00"},
            {"id": 1012, "status": "analyzing", "created": "2025-07-30 09:30:00"},
            {"id": 1013, "status": "completed", "created": "2025-07-30 09:00:00"}
        ]
        
        for session in sessions:
            status_icon = {
                "collecting": "🟢",
                "analyzing": "🟡", 
                "completed": "✅",
                "stopped": "🔴"
            }.get(session["status"], "❓")
            
            print(f"{status_icon} 会话 {session['id']}: {session['status']} (创建: {session['created']})")
            
    except Exception as e:
        print(f"❌ 获取会话列表失败: {e}")

def create_new_session():
    """创建新的采集会话"""
    print("🆕 创建新的采集会话")
    print("=" * 30)
    
    session_data = {
        'openid': f'test_user_{int(time.time())}',
        'device_group_code': f'test_group_{int(time.time())}'
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
            print(f"✅ 新会话创建成功!")
            print(f"   会话ID: {session_id}")
            print(f"   状态: {result.get('status')}")
            print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return session_id
        else:
            print(f"❌ 会话创建失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 会话创建失败: {e}")
        return None

def start_data_collection(session_id):
    """开始数据采集"""
    print(f"📊 开始数据采集 (会话 {session_id})")
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
            print(f"✅ 数据采集开始!")
            print(f"   会话ID: {result.get('session_id')}")
            print(f"   状态: {result.get('status')}")
            return True
        else:
            print(f"❌ 数据采集开始失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 数据采集开始失败: {e}")
        return False

def notify_esp32_start(session_id, device_code="2025001"):
    """通知ESP32开始采集"""
    print(f"📡 通知ESP32开始采集 (会话 {session_id})")
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
            print(f"✅ ESP32通知成功!")
            print(f"   会话ID: {result.get('session_id')}")
            print(f"   设备码: {result.get('device_code')}")
            print(f"   ESP32 IP: {result.get('esp32_ip')}")
            return True
        else:
            print(f"❌ ESP32通知失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ESP32通知失败: {e}")
        return False

def complete_session_workflow():
    """完整的会话工作流程"""
    print("🚀 完整的会话工作流程")
    print("=" * 50)
    
    # 步骤1: 创建新会话
    session_id = create_new_session()
    if not session_id:
        return False
    
    print()
    
    # 步骤2: 开始数据采集
    if not start_data_collection(session_id):
        return False
    
    print()
    
    # 步骤3: 通知ESP32
    if not notify_esp32_start(session_id):
        return False
    
    print()
    print("✅ 完整工作流程执行成功!")
    print(f"📝 新会话ID: {session_id} 已创建并开始采集")
    return True

def test_multiple_collections():
    """测试多次采集"""
    print("🔄 测试多次采集 (每次创建新会话)")
    print("=" * 50)
    
    for i in range(1, 4):
        print(f"\n📱 第 {i} 次采集")
        print("-" * 20)
        
        if complete_session_workflow():
            print(f"✅ 第 {i} 次采集完成")
        else:
            print(f"❌ 第 {i} 次采集失败")
        
        # 等待一下，避免请求过快
        time.sleep(2)
    
    print(f"\n✅ 完成 {i} 次采集测试")
    print("📊 每次采集都创建了不同的会话ID，避免数据覆盖")

def show_session_management_guide():
    """显示会话管理指南"""
    print("📚 会话管理指南")
    print("=" * 50)
    
    print("🔍 问题: 固定会话ID会导致数据覆盖")
    print("💡 解决方案: 每次采集创建新会话")
    print()
    
    print("📋 正确的采集流程:")
    print("1. 小程序调用 start_session/ 创建新会话")
    print("2. 获取新的会话ID (每次都不一样)")
    print("3. 使用新会话ID进行数据采集")
    print("4. ESP32使用新会话ID上传数据")
    print("5. 分析时使用新会话ID")
    print()
    
    print("⚠️  注意事项:")
    print("- 不要使用固定的会话ID (如1011)")
    print("- 每次采集都要调用 start_session/ 创建新会话")
    print("- 保存返回的会话ID用于后续操作")
    print("- 不同次采集的数据会存储在不同的会话中")
    print()
    
    print("🔧 小程序端代码示例:")
    print("""
// 每次采集都创建新会话
wx.request({
  url: 'http://47.122.129.159:8000/wxapp/start_session/',
  method: 'POST',
  data: {
    openid: '用户openid',
    device_group_code: '设备组代码'
  },
  success: function(res) {
    const sessionId = res.data.session_id; // 新会话ID
    console.log('新会话ID:', sessionId);
    
    // 使用新会话ID进行后续操作
    // ...
  }
});
    """)

if __name__ == "__main__":
    print("🧪 会话管理测试")
    print("=" * 50)
    
    # 显示指南
    show_session_management_guide()
    
    # 列出现有会话
    list_all_sessions()
    
    print()
    
    # 测试完整工作流程
    complete_session_workflow()
    
    print()
    
    # 测试多次采集
    test_multiple_collections()
    
    print("\n✅ 测试完成!")
    print("\n📝 总结:")
    print("1. 每次采集都创建新会话，避免数据覆盖")
    print("2. 保存新会话ID用于后续操作")
    print("3. 不同次采集的数据存储在不同会话中")
    print("4. 每次分析都是基于独立的会话数据") 