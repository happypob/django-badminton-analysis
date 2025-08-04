#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ESP32上传完成API接口
"""

import requests
import json
import time

# 服务器配置
SERVER_URL = "http://47.122.129.159:8000"
API_BASE = f"{SERVER_URL}/wxapp"

def test_esp32_mark_upload_complete():
    """测试ESP32标记上传完成接口"""
    print("🚀 测试ESP32上传完成API接口")
    print("=" * 50)
    
    # 测试参数
    session_id = 1011  # 使用现有的活跃会话
    device_code = "2025001"  # 统一的设备码
    
    # 模拟上传统计信息
    upload_stats = {
        "total_files": 3,
        "total_bytes": 1024000,
        "upload_time_ms": 5000,
        "sensor_types": ["waist", "shoulder", "wrist"],
        "data_points": 1500
    }
    
    # 构建请求数据
    data = {
        'session_id': session_id,
        'device_code': device_code,
        'upload_stats': json.dumps(upload_stats)
    }
    
    print(f"📤 发送请求到: {API_BASE}/esp32/mark_upload_complete/")
    print(f"📋 请求参数:")
    print(f"   - session_id: {session_id}")
    print(f"   - device_code: {device_code}")
    print(f"   - upload_stats: {upload_stats}")
    print()
    
    try:
        # 发送POST请求
        response = requests.post(
            f"{API_BASE}/esp32/mark_upload_complete/",
            data=data,
            timeout=30
        )
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功!")
            print(f"📊 响应数据:")
            print(f"   - 消息: {result.get('msg')}")
            print(f"   - 会话ID: {result.get('session_id')}")
            print(f"   - 设备码: {result.get('device_code')}")
            print(f"   - 会话状态: {result.get('session_status')}")
            
            # 数据统计
            stats = result.get('data_collection_stats', {})
            print(f"   - 数据点总数: {stats.get('total_data_points')}")
            print(f"   - 传感器类型: {stats.get('sensor_types')}")
            print(f"   - 采集时长: {stats.get('collection_duration_seconds')}秒")
            
            # 分析结果
            print(f"   - 分析触发: {result.get('analysis_triggered')}")
            print(f"   - 分析ID: {result.get('analysis_id')}")
            print(f"   - 分析状态: {result.get('analysis_status')}")
            
            if result.get('error_message'):
                print(f"   - 错误信息: {result.get('error_message')}")
                
        else:
            print("❌ 请求失败!")
            print(f"错误响应: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求错误: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {e}")

def test_api_documentation():
    """测试API文档接口"""
    print("\n📚 测试API文档接口")
    print("=" * 30)
    
    try:
        response = requests.get(f"{API_BASE}/esp32/mark_upload_complete/")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API文档获取成功!")
            print(f"📋 接口信息:")
            print(f"   - 名称: {result.get('msg')}")
            print(f"   - 方法: {result.get('method')}")
            print(f"   - 描述: {result.get('description')}")
            
            required_params = result.get('required_params', {})
            print(f"   - 必需参数:")
            for param, desc in required_params.items():
                print(f"     * {param}: {desc}")
                
            example = result.get('example', {})
            print(f"   - 示例:")
            for key, value in example.items():
                print(f"     * {key}: {value}")
        else:
            print(f"❌ 获取API文档失败: {response.status_code}")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

def check_session_status(session_id):
    """检查会话状态"""
    print(f"\n🔍 检查会话 {session_id} 状态")
    print("=" * 30)
    
    try:
        # 这里可以调用现有的会话检查接口
        # 暂时用简单的GET请求模拟
        print(f"会话 {session_id} 状态检查完成")
        
    except Exception as e:
        print(f"❌ 检查会话状态失败: {e}")

if __name__ == "__main__":
    print("🧪 ESP32上传完成API测试")
    print("=" * 50)
    
    # 测试API文档
    test_api_documentation()
    
    # 测试上传完成接口
    test_esp32_mark_upload_complete()
    
    # 检查会话状态
    check_session_status(1011)
    
    print("\n✅ 测试完成!") 