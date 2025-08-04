#!/usr/bin/env python3
"""
Django服务器监控脚本
用于检查后端服务状态、API接口、数据库等
"""

import requests
import json
import time
import subprocess
import sys
from datetime import datetime

# 服务器配置
SERVER_URL = "http://47.122.129.159:8000"
API_ENDPOINTS = [
    "/",
    "/wxapp/simple_login/",
    "/wxapp/esp32/upload/",
    "/admin/"
]

def check_server_status():
    """检查服务器基本状态"""
    print("🔍 检查服务器状态...")
    print("=" * 50)
    
    try:
        response = requests.get(SERVER_URL, timeout=10)
        if response.status_code == 200:
            print(f"✅ 服务器运行正常 (状态码: {response.status_code})")
            return True
        else:
            print(f"⚠️ 服务器响应异常 (状态码: {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 服务器连接失败: {e}")
        return False

def check_api_endpoints():
    """检查API接口状态"""
    print("\n🔍 检查API接口状态...")
    print("=" * 50)
    
    results = {}
    
    for endpoint in API_ENDPOINTS:
        try:
            url = f"{SERVER_URL}{endpoint}"
            if endpoint == "/wxapp/simple_login/":
                response = requests.post(url, timeout=10)
            else:
                response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - 正常")
                results[endpoint] = "正常"
            else:
                print(f"⚠️ {endpoint} - 异常 (状态码: {response.status_code})")
                results[endpoint] = f"异常 ({response.status_code})"
                
        except Exception as e:
            print(f"❌ {endpoint} - 失败: {e}")
            results[endpoint] = f"失败 ({str(e)})"
    
    return results

def test_esp32_upload():
    """测试ESP32数据上传接口"""
    print("\n🔍 测试ESP32数据上传...")
    print("=" * 50)
    
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
        
        if response.status_code == 200:
            result = response.json()
            print("✅ ESP32数据上传测试成功!")
            print(f"   响应: {result}")
            return True
        else:
            print(f"❌ ESP32数据上传测试失败 (状态码: {response.status_code})")
            print(f"   错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ESP32数据上传测试异常: {e}")
        return False

def check_database_status():
    """检查数据库状态"""
    print("\n🔍 检查数据库状态...")
    print("=" * 50)
    
    try:
        # 测试数据库连接
        response = requests.get(f"{SERVER_URL}/admin/", timeout=10)
        if response.status_code == 200:
            print("✅ 数据库连接正常")
            return True
        else:
            print(f"⚠️ 数据库连接异常 (状态码: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False

def check_system_resources():
    """检查系统资源"""
    print("\n🔍 检查系统资源...")
    print("=" * 50)
    
    try:
        # 检查磁盘空间
        result = subprocess.run(['df', '-h'], capture_output=True, text=True)
        if result.returncode == 0:
            print("📊 磁盘使用情况:")
            print(result.stdout)
        
        # 检查内存使用
        result = subprocess.run(['free', '-h'], capture_output=True, text=True)
        if result.returncode == 0:
            print("📊 内存使用情况:")
            print(result.stdout)
            
    except Exception as e:
        print(f"❌ 系统资源检查失败: {e}")

def check_process_status():
    """检查Django进程状态"""
    print("\n🔍 检查Django进程状态...")
    print("=" * 50)
    
    try:
        # 检查Python进程
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            django_processes = [line for line in lines if 'python' in line and 'manage.py' in line]
            
            if django_processes:
                print("✅ 发现Django进程:")
                for process in django_processes:
                    print(f"   {process}")
            else:
                print("⚠️ 未发现Django进程")
                
    except Exception as e:
        print(f"❌ 进程检查失败: {e}")

def generate_report():
    """生成监控报告"""
    print("\n📊 生成监控报告...")
    print("=" * 50)
    
    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "server_status": check_server_status(),
        "api_status": check_api_endpoints(),
        "esp32_upload": test_esp32_upload(),
        "database_status": check_database_status()
    }
    
    print("\n📋 监控报告:")
    print(f"   时间: {report['timestamp']}")
    print(f"   服务器状态: {'正常' if report['server_status'] else '异常'}")
    print(f"   ESP32上传: {'正常' if report['esp32_upload'] else '异常'}")
    print(f"   数据库状态: {'正常' if report['database_status'] else '异常'}")
    
    return report

def continuous_monitor(interval=60):
    """持续监控"""
    print(f"\n🔄 开始持续监控 (间隔: {interval}秒)")
    print("按 Ctrl+C 停止监控")
    print("=" * 50)
    
    try:
        while True:
            print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - 执行监控检查")
            generate_report()
            print(f"⏳ 等待 {interval} 秒...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n🛑 监控已停止")

def main():
    """主函数"""
    print("🚀 Django服务器监控工具")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        continuous_monitor()
    else:
        # 单次检查
        generate_report()
        check_system_resources()
        check_process_status()
        
        print("\n🎉 监控检查完成!")

if __name__ == "__main__":
    main() 