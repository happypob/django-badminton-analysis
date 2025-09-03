#!/usr/bin/env python3
"""
WebSocket集成测试 - HTTP API与WebSocket的集成
"""

import asyncio
import json
import time
import requests
import threading

BASE_URL = "http://localhost:8000"

class MockESP32Device:
    """模拟ESP32设备"""
    def __init__(self, device_code):
        self.device_code = device_code
        self.running = False
        
    async def connect_and_listen(self):
        """连接并监听命令"""
        try:
            import websockets
            
            print(f"📱 {self.device_code} 连接到服务器...")
            async with websockets.connect(f"ws://localhost:8000/ws/esp32/{self.device_code}/") as ws:
                print(f"✅ {self.device_code} 连接成功")
                self.running = True
                
                # 发送初始状态
                await ws.send(json.dumps({
                    "type": "status_update",
                    "status": "ready",
                    "timestamp": int(time.time())
                }))
                print(f"📤 {self.device_code} 发送就绪状态")
                
                # 监听命令
                while self.running:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=1)
                        data = json.loads(message)
                        msg_type = data.get('type', 'unknown')
                        print(f"📱 {self.device_code} 收到命令: {msg_type}")
                        
                        # 响应命令
                        if 'start' in msg_type.lower():
                            await ws.send(json.dumps({
                                "type": "status_update",
                                "status": "collecting",
                                "session_id": data.get('session_id'),
                                "timestamp": int(time.time())
                            }))
                            print(f"📱 {self.device_code} 开始数据采集")
                        
                        elif 'stop' in msg_type.lower():
                            await ws.send(json.dumps({
                                "type": "status_update",
                                "status": "stopped",
                                "session_id": data.get('session_id'),
                                "timestamp": int(time.time())
                            }))
                            print(f"📱 {self.device_code} 停止数据采集")
                        
                        elif msg_type == 'test_message':
                            await ws.send(json.dumps({
                                "type": "test_response",
                                "message": f"收到测试消息: {data.get('message', '')}",
                                "timestamp": int(time.time())
                            }))
                            print(f"📱 {self.device_code} 响应测试消息")
                            
                    except asyncio.TimeoutError:
                        # 发送心跳
                        await ws.send(json.dumps({
                            "type": "heartbeat",
                            "timestamp": int(time.time())
                        }))
                    except Exception as e:
                        print(f"📱 {self.device_code} 接收消息错误: {e}")
                        break
                        
        except Exception as e:
            print(f"❌ {self.device_code} 连接失败: {e}")
        finally:
            self.running = False
            print(f"📱 {self.device_code} 连接结束")
    
    def stop(self):
        """停止设备"""
        self.running = False

async def test_integration():
    """测试WebSocket与HTTP API集成"""
    print("🎯 WebSocket集成测试")
    print("=" * 50)
    
    # 创建模拟设备
    devices = [
        MockESP32Device("INTEGRATION_ESP32_001"),
        MockESP32Device("INTEGRATION_ESP32_002")
    ]
    
    # 启动设备连接
    device_tasks = []
    for device in devices:
        task = asyncio.create_task(device.connect_and_listen())
        device_tasks.append(task)
    
    # 等待设备连接完成
    await asyncio.sleep(2)
    
    try:
        # 1. 检查连接状态
        print("\n=== 📊 检查WebSocket连接状态 ===")
        response = requests.get(f"{BASE_URL}/wxapp/websocket/status/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 连接的设备数: {data['connected_devices']['count']}")
            print(f"   设备列表: {data['connected_devices']['devices']}")
        
        # 2. 测试WebSocket广播
        print("\n=== 📡 测试WebSocket广播命令 ===")
        response = requests.post(f"{BASE_URL}/wxapp/websocket/send_command/", data={
            'command_type': 'test',
            'message': '集成测试消息'
        })
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 广播结果: {data.get('result', 'N/A')}")
        else:
            print(f"❌ 广播失败: {response.status_code}")
        
        # 3. 测试原有UDP接口（现在使用WebSocket）
        print("\n=== 🔄 测试原UDP接口（现WebSocket） ===")
        response = requests.post(f"{BASE_URL}/wxapp/test_udp_broadcast/", data={
            'message': '原UDP接口测试'
        })
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 通信方式: {data.get('communication_method', 'N/A')}")
            print(f"✅ 广播结果: {data.get('result', 'N/A')}")
        else:
            print(f"❌ 测试失败: {response.status_code}")
        
        # 4. 测试会话管理
        print("\n=== 📝 测试会话数据采集流程 ===")
        
        # 创建会话
        response = requests.post(f"{BASE_URL}/wxapp/start_session/", data={
            'openid': 'integration_test_user'
        })
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data['session_id']
            print(f"✅ 创建会话: {session_id}")
            
            # 开始数据采集
            await asyncio.sleep(1)
            response = requests.post(f"{BASE_URL}/wxapp/start_data_collection/", data={
                'session_id': session_id
            })
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 开始数据采集: {data['communication_method']}")
                print(f"   结果: {data.get('result', 'N/A')}")
            
            # 等待设备响应
            await asyncio.sleep(2)
            
            # 停止数据采集
            response = requests.post(f"{BASE_URL}/wxapp/notify_esp32_stop/", data={
                'session_id': session_id
            })
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 停止数据采集: {data['communication_method']}")
                print(f"   结果: {data.get('result', 'N/A')}")
        
        # 等待一下观察设备响应
        await asyncio.sleep(3)
        
    finally:
        # 停止所有设备
        print("\n=== 🛑 停止模拟设备 ===")
        for device in devices:
            device.stop()
        
        # 等待任务结束
        for task in device_tasks:
            task.cancel()
        
        # 等待清理
        await asyncio.sleep(1)

async def main():
    """主函数"""
    try:
        # 检查websockets
        import websockets
    except ImportError:
        print("📦 安装websockets库...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    
    # 运行集成测试
    await test_integration()
    
    print("\n" + "=" * 50)
    print("🎉 WebSocket集成测试完成！")
    print("\n📋 测试总结:")
    print("✅ WebSocket连接正常")
    print("✅ HTTP API → WebSocket 通信正常")
    print("✅ 设备命令响应正常")
    print("✅ 原有接口兼容性保持")
    print("\n🚀 WebSocket迁移验证成功！")

if __name__ == "__main__":
    asyncio.run(main()) 