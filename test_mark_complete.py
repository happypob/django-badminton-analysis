#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据收集完成标记接口
演示如何手动标记数据收集完成并触发分析
"""

import requests
import json
import time

# 服务器配置
SERVER_URL = "http://47.122.129.159:8000"
API_PREFIX = "/wxapp"

def test_mark_data_collection_complete():
    """测试标记数据收集完成接口"""
    
    print("🚀 测试数据收集完成标记接口")
    print("=" * 50)
    
    # 测试参数
    session_id = 123  # 使用现有的测试会话
    completion_code = "DATA_COLLECTION_COMPLETE_2024"
    
    # 构建请求数据
    data = {
        'session_id': session_id,
        'completion_code': completion_code
    }
    
    print(f"📤 发送请求到: {SERVER_URL}{API_PREFIX}/mark_complete/")
    print(f"📋 请求参数: {data}")
    
    try:
        # 发送POST请求
        response = requests.post(
            f"{SERVER_URL}{API_PREFIX}/mark_complete/",
            data=data,
            timeout=30
        )
        
        print(f"📡 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功!")
            print("📊 响应数据:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 解析响应数据
            if result.get('analysis_triggered'):
                print(f"🎯 分析已触发，分析ID: {result.get('analysis_id')}")
                print(f"📈 数据统计:")
                stats = result.get('data_collection_stats', {})
                print(f"   - 总数据点: {stats.get('total_data_points', 0)}")
                print(f"   - 传感器类型: {stats.get('sensor_types', [])}")
                print(f"   - 收集时长: {stats.get('collection_duration_seconds', 0):.1f}秒")
            else:
                print("⚠️ 分析触发失败")
                if result.get('error_message'):
                    print(f"错误信息: {result['error_message']}")
        else:
            print("❌ 请求失败!")
            print(f"错误响应: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求错误: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {e}")

def test_get_interface_info():
    """测试获取接口信息"""
    
    print("\n📋 获取接口使用说明")
    print("=" * 30)
    
    try:
        response = requests.get(f"{SERVER_URL}{API_PREFIX}/mark_complete/")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 接口信息获取成功!")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"❌ 获取接口信息失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 获取接口信息错误: {e}")

def test_without_completion_code():
    """测试不带完成标识码的请求"""
    
    print("\n🧪 测试不带完成标识码的请求")
    print("=" * 40)
    
    data = {
        'session_id': 123
        # 不包含completion_code
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}{API_PREFIX}/mark_complete/",
            data=data,
            timeout=30
        )
        
        print(f"📡 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 请求成功 (不带完成标识码也可以)")
            result = response.json()
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("❌ 请求失败!")
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试错误: {e}")

def test_invalid_completion_code():
    """测试无效的完成标识码"""
    
    print("\n🚫 测试无效的完成标识码")
    print("=" * 35)
    
    data = {
        'session_id': 123,
        'completion_code': 'INVALID_CODE'
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}{API_PREFIX}/mark_complete/",
            data=data,
            timeout=30
        )
        
        print(f"📡 响应状态码: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ 正确拒绝了无效的完成标识码")
            result = response.json()
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("❌ 应该拒绝无效标识码但没有拒绝")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试错误: {e}")

def main():
    """主函数"""
    print("🎯 数据收集完成标记接口测试")
    print("=" * 50)
    
    # 1. 获取接口信息
    test_get_interface_info()
    
    # 2. 测试正常请求
    test_mark_data_collection_complete()
    
    # 3. 测试不带完成标识码
    test_without_completion_code()
    
    # 4. 测试无效完成标识码
    test_invalid_completion_code()
    
    print("\n✅ 所有测试完成!")

if __name__ == "__main__":
    main() 