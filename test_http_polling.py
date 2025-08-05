#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP轮询功能测试脚本
"""

import requests
import json
import time

# 服务器配置
SERVER_URL = "http://localhost:8000"

def test_esp32_polling():
    """测试ESP32轮询功能"""
    print("🚀 ESP32 HTTP轮询功能测试")
    print("=" * 50)
    
    device_code = "2025001"
    
    # 1. 测试轮询API（无指令状态）
    print("\n📡 测试1: ESP32轮询（无指令状态）")
    try:
        response = requests.post(f"{SERVER_URL}/wxapp/esp32/poll_commands/", data={
            'device_code': device_code,
            'current_session': '',
            'status': 'idle'
        }, timeout=10)
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('command') is None:
                print("✅ 无指令状态正常")
            else:
                print(f"⚠️  收到指令: {result.get('command')}")
        else:
            print("❌ 轮询失败")
            
    except Exception as e:
        print(f"❌ 轮询测试失败: {str(e)}")
    
    # 2. 创建采集会话
    print("\n📱 测试2: 创建采集会话")
    try:
        response = requests.post(f"{SERVER_URL}/wxapp/start_session/", data={
            'openid': 'test_user_123456',
            'device_group_code': device_code,
            'device_code': device_code
        }, timeout=10)
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            session_id = result.get('session_id')
            print(f"✅ 会话创建成功，ID: {session_id}")
            
            # 3. 测试轮询获取开始指令
            print("\n📡 测试3: ESP32轮询获取开始指令")
            time.sleep(2)  # 等待2秒
            
            response = requests.post(f"{SERVER_URL}/wxapp/esp32/poll_commands/", data={
                'device_code': device_code,
                'current_session': '',
                'status': 'idle'
            }, timeout=10)
            
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('command') == 'START_COLLECTION':
                    print("✅ 成功获取开始指令")
                    poll_session_id = result.get('session_id')
                    
                    # 4. 测试ESP32确认开始采集
                    print("\n📤 测试4: ESP32确认开始采集")
                    response = requests.post(f"{SERVER_URL}/wxapp/esp32/status/", data={
                        'status': 'START_COLLECTION_CONFIRMED',
                        'session_id': poll_session_id,
                        'device_code': device_code
                    }, timeout=10)
                    
                    print(f"状态码: {response.status_code}")
                    print(f"响应: {response.text}")
                    
                    # 5. 测试轮询（正在采集状态）
                    print("\n📡 测试5: ESP32轮询（正在采集状态）")
                    response = requests.post(f"{SERVER_URL}/wxapp/esp32/poll_commands/", data={
                        'device_code': device_code,
                        'current_session': poll_session_id,
                        'status': 'collecting'
                    }, timeout=10)
                    
                    print(f"状态码: {response.status_code}")
                    print(f"响应: {response.text}")
                    
                    # 6. 结束采集会话
                    print("\n🛑 测试6: 结束采集会话")
                    response = requests.post(f"{SERVER_URL}/wxapp/end_session/", data={
                        'session_id': session_id,
                        'device_code': device_code
                    }, timeout=10)
                    
                    print(f"状态码: {response.status_code}")
                    print(f"响应: {response.text}")
                    
                    if response.status_code == 200:
                        print("✅ 会话结束成功")
                        
                        # 7. 测试轮询获取停止指令
                        print("\n📡 测试7: ESP32轮询获取停止指令")
                        time.sleep(2)  # 等待2秒
                        
                        response = requests.post(f"{SERVER_URL}/wxapp/esp32/poll_commands/", data={
                            'device_code': device_code,
                            'current_session': poll_session_id,
                            'status': 'collecting'
                        }, timeout=10)
                        
                        print(f"状态码: {response.status_code}")
                        print(f"响应: {response.text}")
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result.get('command') == 'STOP_COLLECTION':
                                print("✅ 成功获取停止指令")
                                
                                # 8. 测试ESP32确认停止采集
                                print("\n📤 测试8: ESP32确认停止采集")
                                response = requests.post(f"{SERVER_URL}/wxapp/esp32/status/", data={
                                    'status': 'STOP_COLLECTION_CONFIRMED',
                                    'session_id': poll_session_id,
                                    'device_code': device_code
                                }, timeout=10)
                                
                                print(f"状态码: {response.status_code}")
                                print(f"响应: {response.text}")
                            else:
                                print("❌ 未获取到停止指令")
                        else:
                            print("❌ 轮询停止指令失败")
                    else:
                        print("❌ 会话结束失败")
                else:
                    print("❌ 未获取到开始指令")
            else:
                print("❌ 轮询开始指令失败")
        else:
            print("❌ 会话创建失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def test_latest_images():
    """测试最新图片获取"""
    print("\n🖼️  测试最新分析图片获取")
    print("-" * 30)
    
    try:
        response = requests.get(f"{SERVER_URL}/wxapp/latest_analysis_images/", timeout=10)
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if 'images' in result:
                print(f"✅ 成功获取 {len(result['images'])} 张图片")
                for i, img in enumerate(result['images']):
                    print(f"   图片{i+1}: {img.get('title')} - {img.get('image_url')}")
            else:
                print("⚠️  响应格式异常")
        else:
            print("❌ 获取图片失败")
            
    except Exception as e:
        print(f"❌ 图片获取测试失败: {str(e)}")

if __name__ == "__main__":
    print("🔍 HTTP轮询功能完整测试")
    print("=" * 50)
    
    # 测试ESP32轮询功能
    test_esp32_polling()
    
    # 测试图片获取
    test_latest_images()
    
    print("\n🎉 测试完成!") 