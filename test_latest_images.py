#!/usr/bin/env python3
"""
测试最新分析图片生成和访问
"""

import requests
import json
import time
from datetime import datetime

# 服务器配置
SERVER_URL = "http://47.122.129.159:8000"

def test_latest_analysis_images():
    """测试获取最新分析图片"""
    print("🖼️ 测试最新分析图片获取")
    print("-" * 50)
    
    try:
        # 获取最新分析图片
        response = requests.get(f"{SERVER_URL}/wxapp/latest_analysis_images/", timeout=10)
        
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

def test_direct_image_access():
    """测试直接访问图片文件"""
    print("\n🖼️ 测试直接访问图片文件")
    print("-" * 50)
    
    image_urls = [
        f"{SERVER_URL}/images/latest_multi_sensor_curve.jpg",
        f"{SERVER_URL}/images/default_analysis.jpg"
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

def test_force_image_generation():
    """测试强制生成最新图片"""
    print("\n🔄 测试强制生成最新图片")
    print("-" * 50)
    
    try:
        # 获取最新会话
        response = requests.get(f"{SERVER_URL}/wxapp/latest_analysis_images/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'latest_analysis' in data:
                session_id = data['latest_analysis']['session_id']
                print(f"📊 最新会话ID: {session_id}")
                
                # 尝试重新生成图片
                print("🔄 尝试重新生成分析图片...")
                # 这里可以添加重新生成图片的逻辑
                
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

if __name__ == "__main__":
    print("🔍 分析图片功能测试")
    print("=" * 50)
    
    # 测试获取最新分析图片
    test_latest_analysis_images()
    
    # 测试直接访问图片
    test_direct_image_access()
    
    # 测试强制生成图片
    test_force_image_generation()
    
    print("\n✅ 测试完成") 