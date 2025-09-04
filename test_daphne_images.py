#!/usr/bin/env python3
"""
Daphne部署图片功能测试脚本
用于验证图片生成、访问和API功能
"""

import requests
import json
import sys
from datetime import datetime

# 配置你的服务器信息
SERVER_IP = "your_server_ip"  # 替换为你的服务器IP
SERVER_PORT = "8000"
BASE_URL = f"http://{SERVER_IP}:{SERVER_PORT}"

def test_server_connection():
    """测试服务器连接"""
    print("🔍 测试服务器连接...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            print("✅ 服务器连接正常")
            return True
        else:
            print(f"❌ 服务器返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def test_debug_api():
    """测试调试API"""
    print("\n🔍 测试调试API...")
    try:
        response = requests.get(f"{BASE_URL}/api/debug_images/", timeout=15)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 调试API正常")
            print(f"   MEDIA_ROOT: {data.get('settings', {}).get('MEDIA_ROOT', 'N/A')}")
            print(f"   MEDIA_URL: {data.get('settings', {}).get('MEDIA_URL', 'N/A')}")
            
            # 显示目录信息
            directories = data.get('directories', {})
            for dir_name, dir_info in directories.items():
                print(f"   {dir_name}: 存在={dir_info.get('exists')}, 可写={dir_info.get('writable')}")
                if dir_info.get('files'):
                    print(f"      文件: {dir_info['files']}")
            
            return True
        else:
            print(f"❌ 调试API失败: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ 调试API测试失败: {e}")
        return False

def test_image_generation():
    """测试图片生成"""
    print("\n🔍 测试图片生成...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/debug_images/", 
            data={'action': 'regenerate'},
            timeout=30
        )
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 图片生成成功")
            print(f"   生成路径: {data.get('test_image_path', 'N/A')}")
            return True
        else:
            print(f"❌ 图片生成失败: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ 图片生成测试失败: {e}")
        return False

def test_miniprogram_api():
    """测试小程序API"""
    print("\n🔍 测试小程序图片API...")
    try:
        response = requests.get(f"{BASE_URL}/api/miniprogram/get_images/", timeout=15)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ 小程序API正常")
                images = data.get('images', [])
                print(f"   找到图片数量: {len(images)}")
                for img in images:
                    print(f"   - {img.get('filename')}: {img.get('url')}")
                return True
            else:
                print(f"⚠️ 小程序API返回错误: {data.get('error')}")
                return False
        else:
            print(f"❌ 小程序API失败: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ 小程序API测试失败: {e}")
        return False

def test_image_access():
    """测试图片直接访问"""
    print("\n🔍 测试图片直接访问...")
    
    # 常见的图片文件名
    image_files = [
        'latest_multi_sensor_curve.jpg',
        'test_analysis_curve.jpg',
        'debug_test_image.jpg'
    ]
    
    accessible_images = []
    
    for filename in image_files:
        try:
            url = f"{BASE_URL}/images/{filename}"
            response = requests.head(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {filename} 可访问")
                accessible_images.append(url)
            else:
                print(f"❌ {filename} 无法访问 (状态码: {response.status_code})")
        except Exception as e:
            print(f"❌ {filename} 测试失败: {e}")
    
    return len(accessible_images) > 0

def test_list_images_api():
    """测试图片列表API"""
    print("\n🔍 测试图片列表API...")
    try:
        response = requests.get(f"{BASE_URL}/api/list_images/", timeout=15)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 图片列表API正常")
            
            media_images = data.get('media_images', [])
            print(f"   MEDIA目录图片数量: {len(media_images)}")
            
            for img in media_images:
                print(f"   - {img['filename']} ({img['size']} bytes)")
                print(f"     URL: {img['url']}")
            
            return True
        else:
            print(f"❌ 图片列表API失败: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ 图片列表API测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 Daphne部署图片功能测试")
    print(f"测试服务器: {BASE_URL}")
    print(f"测试时间: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # 执行测试
    results = []
    
    results.append(("服务器连接", test_server_connection()))
    results.append(("调试API", test_debug_api()))
    results.append(("图片生成", test_image_generation()))
    results.append(("小程序API", test_miniprogram_api()))
    results.append(("图片列表API", test_list_images_api()))
    results.append(("图片直接访问", test_image_access()))
    
    # 显示测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:15} : {status}")
        if result:
            passed += 1
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    # 提供建议
    print("\n" + "=" * 60)
    print("💡 建议和下一步:")
    print("=" * 60)
    
    if passed == total:
        print("🎉 所有测试通过！图片功能正常工作。")
        print("   小程序可以使用以下API:")
        print(f"   主要API: {BASE_URL}/api/miniprogram/get_images/")
        print(f"   调试API: {BASE_URL}/api/debug_images/")
    else:
        print("⚠️ 部分测试失败，请检查以下问题:")
        
        if not results[0][1]:  # 服务器连接失败
            print(f"   1. 确认Daphne服务正在运行: daphne -b 0.0.0.0 -p {SERVER_PORT} djangodemo.asgi:application")
            print(f"   2. 检查防火墙是否开放端口 {SERVER_PORT}")
            print(f"   3. 确认服务器IP地址: {SERVER_IP}")
        
        if not results[1][1]:  # 调试API失败
            print("   1. 检查Django URL配置")
            print("   2. 确认views.py中的调试函数")
        
        if not results[2][1]:  # 图片生成失败
            print("   1. 检查matplotlib安装: pip install matplotlib")
            print("   2. 确认images目录权限: chmod 755 images/")
            print("   3. 检查磁盘空间")
        
        if not results[4][1]:  # 图片访问失败
            print("   1. 确认Django静态文件配置")
            print("   2. 检查MEDIA_ROOT和MEDIA_URL设置")
    
    print(f"\n测试完成时间: {datetime.now().isoformat()}")

if __name__ == "__main__":
    # 检查是否提供了服务器IP
    if len(sys.argv) > 1:
        SERVER_IP = sys.argv[1]
        BASE_URL = f"http://{SERVER_IP}:{SERVER_PORT}"
        print(f"使用命令行提供的服务器IP: {SERVER_IP}")
    elif SERVER_IP == "your_server_ip":
        print("⚠️ 请修改脚本中的SERVER_IP变量为你的实际服务器IP")
        print("   或者使用命令行参数: python test_daphne_images.py YOUR_SERVER_IP")
        sys.exit(1)
    
    main() 