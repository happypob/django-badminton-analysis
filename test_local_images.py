#!/usr/bin/env python3
"""
测试本地服务器的最新分析图片功能
"""

import requests
import json
import time
from datetime import datetime

# 本地服务器配置
LOCAL_SERVER_URL = "http://localhost:8000"

def test_local_latest_analysis_images():
    """测试本地获取最新分析图片"""
    print("🖼️ 测试本地最新分析图片获取")
    print("-" * 50)
    
    try:
        # 获取最新分析图片
        response = requests.get(f"{LOCAL_SERVER_URL}/wxapp/latest_analysis_images/", timeout=10)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 成功获取分析图片信息")
            
            if 'images' in data and data['images']:
                for i, img in enumerate(data['images']):
                    print(f"\n📊 图片 {i+1}:")
                    print(f"   标题: {img.get('title')}")
                    print(f"   描述: {img.get('description')}")
                    print(f"   图片URL: {img.get('image_url')}")
                    print(f"   分析ID: {img.get('analysis_id')}")
                    print(f"   会话ID: {img.get('session_id')}")
                    print(f"   创建时间: {img.get('created_at')}")
                    
                    # 尝试直接访问图片
                    img_response = requests.get(img.get('image_url'), timeout=10)
                    if img_response.status_code == 200:
                        print(f"   ✅ 图片可正常访问 (大小: {len(img_response.content)} bytes)")
                    else:
                        print(f"   ❌ 图片访问失败 (状态码: {img_response.status_code})")
            else:
                print("⚠️ 暂无分析图片")
                
            if 'latest_analysis' in data:
                analysis = data['latest_analysis']
                print(f"\n📈 最新分析信息:")
                print(f"   分析ID: {analysis.get('id')}")
                print(f"   会话ID: {analysis.get('session_id')}")
                print(f"   状态: {analysis.get('status')}")
                print(f"   创建时间: {analysis.get('created_at')}")
        else:
            print(f"❌ 获取失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def test_local_direct_image_access():
    """测试本地直接访问图片文件"""
    print("\n🖼️ 测试本地直接访问图片文件")
    print("-" * 50)
    
    image_urls = [
        f"{LOCAL_SERVER_URL}/images/latest_multi_sensor_curve.jpg",
        f"{LOCAL_SERVER_URL}/images/default_analysis.jpg"
    ]
    
    for url in image_urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {url} - 可访问 (大小: {len(response.content)} bytes)")
            else:
                print(f"❌ {url} - 访问失败 (状态码: {response.status_code})")
        except Exception as e:
            print(f"❌ {url} - 访问异常: {str(e)}")

def test_local_server_status():
    """测试本地服务器状态"""
    print("\n🌐 测试本地服务器状态")
    print("-" * 50)
    
    try:
        response = requests.get(f"{LOCAL_SERVER_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ 本地服务器运行正常")
            print(f"   响应内容: {response.text[:200]}...")
        else:
            print(f"❌ 本地服务器响应异常 (状态码: {response.status_code})")
    except Exception as e:
        print(f"❌ 本地服务器连接失败: {str(e)}")

if __name__ == "__main__":
    print("🔍 本地分析图片功能测试")
    print("=" * 50)
    
    # 测试本地服务器状态
    test_local_server_status()
    
    # 测试获取最新分析图片
    test_local_latest_analysis_images()
    
    # 测试直接访问图片
    test_local_direct_image_access()
    
    print("\n✅ 本地测试完成") 