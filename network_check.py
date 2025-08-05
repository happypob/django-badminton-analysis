#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络连接检查脚本
"""

import socket
import subprocess
import platform
import requests

def check_network_connectivity():
    """检查网络连接性"""
    print("🔍 网络连接检查")
    print("=" * 50)
    
    # 检查服务器IP
    try:
        # 获取本机IP
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"📡 本机IP: {local_ip}")
        
        # 检查网络接口
        if platform.system() == "Windows":
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
        else:
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        
        print("🌐 网络接口信息:")
        print(result.stdout[:500])  # 只显示前500字符
        
    except Exception as e:
        print(f"❌ 获取网络信息失败: {e}")
    
    # 测试UDP广播
    test_udp_broadcast()

def test_udp_broadcast():
    """测试UDP广播功能"""
    print("\n📡 UDP广播测试")
    print("-" * 30)
    
    try:
        # 创建UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # 测试消息
        test_message = '{"test": "UDP broadcast test"}'
        
        # 发送到广播地址
        broadcast_address = ('255.255.255.255', 8888)
        sock.sendto(test_message.encode(), broadcast_address)
        
        print("✅ UDP广播测试消息已发送")
        print(f"   目标: 255.255.255.255:8888")
        print(f"   消息: {test_message}")
        
        sock.close()
        
    except Exception as e:
        print(f"❌ UDP广播测试失败: {e}")

def check_esp32_network():
    """检查ESP32网络连接"""
    print("\n📱 ESP32网络连接检查")
    print("-" * 30)
    
    print("请确保ESP32:")
    print("1. 连接到与服务器相同的WiFi网络")
    print("2. 获取到有效的IP地址")
    print("3. 能够ping通服务器")
    print("4. 防火墙允许UDP端口8888")
    
    # 检查常见网络问题
    print("\n🔧 常见问题排查:")
    print("1. WiFi密码是否正确")
    print("2. ESP32是否成功获取IP")
    print("3. 服务器和ESP32是否在同一网段")
    print("4. 路由器是否阻止了UDP广播")

def network_troubleshooting():
    """网络故障排除指南"""
    print("\n🛠️  网络故障排除指南")
    print("=" * 50)
    
    print("1. 检查WiFi连接:")
    print("   - ESP32串口显示WiFi连接成功")
    print("   - 获取到有效的IP地址")
    
    print("\n2. 检查网络配置:")
    print("   - 服务器IP: 172.18.48.119")
    print("   - ESP32应该在同一网段")
    print("   - 例如: 172.18.48.x")
    
    print("\n3. 测试网络连通性:")
    print("   - 在ESP32上ping服务器IP")
    print("   - 检查UDP端口8888是否开放")
    
    print("\n4. 防火墙设置:")
    print("   - 确保UDP端口8888未被阻止")
    print("   - 检查路由器UDP广播设置")

if __name__ == "__main__":
    check_network_connectivity()
    check_esp32_network()
    network_troubleshooting() 