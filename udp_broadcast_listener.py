#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UDP广播监听器 - 用于监听服务器发送的UDP广播
"""

import socket
import json
import threading
import time
from datetime import datetime

# UDP广播配置
UDP_BROADCAST_PORT = 8888
UDP_BROADCAST_ADDRESS = "255.255.255.255"

class UDPBroadcastListener:
    def __init__(self):
        self.socket = None
        self.is_listening = False
        
    def start_listening(self):
        """开始监听UDP广播"""
        try:
            # 创建UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # 绑定到广播端口
            self.socket.bind(('', UDP_BROADCAST_PORT))
            
            print(f"🔍 开始监听UDP广播...")
            print(f"📍 监听地址: 0.0.0.0:{UDP_BROADCAST_PORT}")
            print(f"📡 广播地址: {UDP_BROADCAST_ADDRESS}:{UDP_BROADCAST_PORT}")
            print("=" * 60)
            
            self.is_listening = True
            
            while self.is_listening:
                try:
                    # 接收数据
                    data, addr = self.socket.recvfrom(1024)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    print(f"\n📨 [{timestamp}] 收到UDP广播")
                    print(f"📡 来源: {addr[0]}:{addr[1]}")
                    print(f"📦 数据长度: {len(data)} 字节")
                    
                    try:
                        # 尝试解析JSON
                        message = data.decode('utf-8')
                        json_data = json.loads(message)
                        
                        print("📋 解析的JSON数据:")
                        print(json.dumps(json_data, indent=2, ensure_ascii=False))
                        
                        # 分析消息类型
                        command = json_data.get('command', '')
                        if command == 'START_COLLECTION':
                            print("🟢 检测到: 开始采集指令")
                            print(f"   会话ID: {json_data.get('session_id')}")
                            print(f"   设备码: {json_data.get('device_code')}")
                        elif command == 'STOP_COLLECTION':
                            print("🔴 检测到: 停止采集指令")
                            print(f"   会话ID: {json_data.get('session_id')}")
                            print(f"   设备码: {json_data.get('device_code')}")
                        else:
                            print(f"❓ 未知指令: {command}")
                            
                    except json.JSONDecodeError:
                        print("❌ 无法解析JSON数据")
                        print(f"📄 原始数据: {data}")
                    except UnicodeDecodeError:
                        print("❌ 无法解码UTF-8数据")
                        print(f"📄 原始数据: {data}")
                        
                    print("-" * 60)
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"❌ 接收数据时出错: {str(e)}")
                    break
                    
        except Exception as e:
            print(f"❌ 启动监听失败: {str(e)}")
        finally:
            self.stop_listening()
    
    def stop_listening(self):
        """停止监听"""
        self.is_listening = False
        if self.socket:
            self.socket.close()
            print("\n🛑 UDP广播监听已停止")

def main():
    """主函数"""
    listener = UDPBroadcastListener()
    
    try:
        # 启动监听线程
        listen_thread = threading.Thread(target=listener.start_listening)
        listen_thread.daemon = True
        listen_thread.start()
        
        print("💡 提示:")
        print("   - 按 Ctrl+C 停止监听")
        print("   - 在另一个终端测试UDP广播")
        print("   - 监听器会显示所有收到的广播消息")
        print()
        
        # 保持主线程运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号...")
        listener.stop_listening()
        print("✅ 监听器已安全停止")

if __name__ == "__main__":
    main() 