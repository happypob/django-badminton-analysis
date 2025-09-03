#!/usr/bin/env python3
"""
简单WebSocket客户端测试
"""

import asyncio
import json
import time

async def test_esp32_websocket():
    """测试ESP32 WebSocket连接"""
    try:
        import websockets
        
        print("🔌 连接ESP32 WebSocket...")
        async with websockets.connect("ws://localhost:8000/ws/esp32/TEST_ESP32_001/") as websocket:
            print("✅ ESP32连接成功")
            
            # 发送心跳
            heartbeat = {
                "type": "heartbeat",
                "timestamp": int(time.time())
            }
            await websocket.send(json.dumps(heartbeat))
            print("📤 发送心跳")
            
            # 发送状态更新
            status = {
                "type": "status_update",
                "status": "ready",
                "timestamp": int(time.time())
            }
            await websocket.send(json.dumps(status))
            print("📤 发送状态更新: ready")
            
            # 等待响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                print(f"📥 收到响应: {data.get('type', 'unknown')}")
            except asyncio.TimeoutError:
                print("⏰ 响应超时（正常，没有客户端命令）")
            
            print("✅ ESP32 WebSocket测试完成")
            return True
            
    except ImportError:
        print("❌ 请安装websockets: pip install websockets")
        return False
    except Exception as e:
        print(f"❌ ESP32连接失败: {e}")
        return False

async def test_miniprogram_websocket():
    """测试小程序 WebSocket连接"""
    try:
        import websockets
        
        print("\n🔌 连接小程序 WebSocket...")
        async with websockets.connect("ws://localhost:8000/ws/miniprogram/test_user_001/") as websocket:
            print("✅ 小程序连接成功")
            
            # 发送会话查询
            query = {
                "type": "session_status",
                "session_id": 1
            }
            await websocket.send(json.dumps(query))
            print("📤 发送会话状态查询")
            
            # 等待响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                print(f"📥 收到响应: {data.get('type', 'unknown')}")
            except asyncio.TimeoutError:
                print("⏰ 响应超时（正常，可能没有对应会话）")
            
            print("✅ 小程序 WebSocket测试完成")
            return True
            
    except Exception as e:
        print(f"❌ 小程序连接失败: {e}")
        return False

async def test_admin_websocket():
    """测试管理员 WebSocket连接"""
    try:
        import websockets
        
        print("\n🔌 连接管理员 WebSocket...")
        async with websockets.connect("ws://localhost:8000/ws/admin/") as websocket:
            print("✅ 管理员连接成功")
            
            # 获取系统状态
            query = {
                "type": "get_system_status"
            }
            await websocket.send(json.dumps(query))
            print("📤 请求系统状态")
            
            # 等待响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                print(f"📥 收到响应: {data.get('type', 'unknown')}")
                if data.get('type') == 'system_status':
                    status = data.get('status', {})
                    print(f"   📊 系统状态: {status.get('status', 'unknown')}")
            except asyncio.TimeoutError:
                print("⏰ 响应超时")
            
            print("✅ 管理员 WebSocket测试完成")
            return True
            
    except Exception as e:
        print(f"❌ 管理员连接失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🎯 WebSocket客户端连接测试")
    print("=" * 40)
    
    # 安装websockets
    try:
        import websockets
    except ImportError:
        print("📦 安装websockets库...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
        import websockets
    
    # 运行所有测试
    results = []
    results.append(await test_esp32_websocket())
    results.append(await test_miniprogram_websocket())
    results.append(await test_admin_websocket())
    
    # 总结结果
    print("\n" + "=" * 40)
    print("📊 WebSocket连接测试结果:")
    connection_types = ["ESP32", "小程序", "管理员"]
    for i, result in enumerate(results):
        status = "✅" if result else "❌"
        print(f"   {connection_types[i]}: {status}")
    
    success_count = sum(results)
    if success_count == len(results):
        print("🎉 所有WebSocket连接测试成功！")
    else:
        print(f"⚠️  {success_count}/{len(results)} 个连接成功")
    
    print("\n💡 现在可以测试HTTP API与WebSocket的集成了")

if __name__ == "__main__":
    asyncio.run(main()) 