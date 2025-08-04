#!/usr/bin/env python3
"""
检查Django POST请求的简单脚本
"""

import requests
import json
import time
from datetime import datetime

# 服务器配置
SERVER_URL = "http://47.122.129.159:8000"

def test_simple_login():
    """测试小程序登录POST请求"""
    print("🔍 测试小程序登录POST请求...")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/wxapp/simple_login/",
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            print("✅ 小程序登录接口正常")
            return True
        else:
            print("❌ 小程序登录接口异常")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_esp32_upload():
    """测试ESP32数据上传POST请求"""
    print("\n🔍 测试ESP32数据上传POST请求...")
    
    test_data = {
        "device_code": "2025001",
        "sensor_type": "waist",
        "data": json.dumps({
            "acc": [1.2, 0.8, 9.8],
            "gyro": [0.1, 0.2, 0.3],
            "angle": [45.0, 30.0, 60.0]
        }),
        "session_id": "123",
        "timestamp": str(int(time.time()))
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/wxapp/esp32/upload/",
            data=test_data,
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            print("✅ ESP32数据上传接口正常")
            return True
        else:
            print("❌ ESP32数据上传接口异常")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_server_status():
    """测试服务器基本状态"""
    print("🔍 测试服务器基本状态...")
    
    try:
        response = requests.get(SERVER_URL, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            return True
        else:
            print("❌ 服务器响应异常")
            return False
            
    except Exception as e:
        print(f"❌ 服务器连接失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Django POST请求检查工具")
    print("=" * 50)
    print(f"服务器地址: {SERVER_URL}")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 1. 检查服务器状态
    server_ok = test_server_status()
    
    if server_ok:
        # 2. 测试小程序登录
        login_ok = test_simple_login()
        
        # 3. 测试ESP32上传
        upload_ok = test_esp32_upload()
        
        print("\n📊 检查结果:")
        print(f"   服务器状态: {'正常' if server_ok else '异常'}")
        print(f"   小程序登录: {'正常' if login_ok else '异常'}")
        print(f"   ESP32上传: {'正常' if upload_ok else '异常'}")
    else:
        print("\n❌ 服务器无法连接，请检查Django服务是否运行")

if __name__ == "__main__":
    main() 