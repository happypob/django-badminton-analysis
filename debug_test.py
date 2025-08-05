#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试测试脚本
"""

import requests
import time

SERVER_URL = "http://localhost:8000"
device_code = "2025001"

def debug_test():
    """调试测试"""
    print("🔍 调试测试")
    print("=" * 30)
    
    # 1. 创建会话
    print("📱 1. 创建采集会话")
    response = requests.post(f"{SERVER_URL}/wxapp/start_session/", data={
        'openid': 'test_user_123456',
        'device_group_code': device_code,
        'device_code': device_code
    })
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        session_id = result.get('session_id')
        print(f"✅ 会话创建成功: {session_id}")
        
        # 2. 轮询获取开始指令
        print("\n📡 2. 轮询获取开始指令")
        response = requests.post(f"{SERVER_URL}/wxapp/esp32/poll_commands/", data={
            'device_code': device_code,
            'current_session': '',
            'status': 'idle'
        })
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            poll_session_id = result.get('session_id')
            command = result.get('command')
            print(f"✅ 轮询结果: command={command}, session_id={poll_session_id}")
            
            if command == 'START_COLLECTION':
                print("✅ 成功获取开始指令")
                
                # 3. 结束会话
                print("\n🛑 3. 结束采集会话")
                response = requests.post(f"{SERVER_URL}/wxapp/end_session/", data={
                    'session_id': session_id,
                    'device_code': device_code
                })
                
                print(f"状态码: {response.status_code}")
                print(f"响应: {response.text}")
                
                if response.status_code == 200:
                    print("✅ 会话结束成功")
                    
                    # 4. 轮询获取停止指令
                    print("\n📡 4. 轮询获取停止指令")
                    response = requests.post(f"{SERVER_URL}/wxapp/esp32/poll_commands/", data={
                        'device_code': device_code,
                        'current_session': poll_session_id,
                        'status': 'collecting'
                    })
                    
                    print(f"状态码: {response.status_code}")
                    print(f"响应: {response.text}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        command = result.get('command')
                        print(f"✅ 轮询结果: command={command}")
                        
                        if command == 'STOP_COLLECTION':
                            print("🎉 成功获取停止指令!")
                        else:
                            print("❌ 未获取到停止指令")
                    else:
                        print("❌ 轮询失败")
                else:
                    print("❌ 会话结束失败")
            else:
                print("❌ 未获取到开始指令")
        else:
            print("❌ 轮询开始指令失败")
    else:
        print("❌ 会话创建失败")

if __name__ == "__main__":
    debug_test() 