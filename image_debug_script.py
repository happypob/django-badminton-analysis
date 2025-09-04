#!/usr/bin/env python3
"""
羽毛球分析系统 - 图片调试脚本
用于在CentOS服务器上调试图片生成和访问问题
"""

import os
import sys
import requests
import json
from datetime import datetime

# 添加Django项目路径
sys.path.insert(0, '/path/to/your/project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangodemo.settings')

import django
django.setup()

from django.conf import settings
from wxapp.models import AnalysisResult, DataCollectionSession
from wxapp.views import generate_test_image, generate_multi_sensor_curve
import matplotlib
matplotlib.use('Agg')  # 使用无GUI后端

def check_system_info():
    """检查系统基本信息"""
    print("🔍 系统信息检查")
    print("=" * 50)
    
    print(f"Python版本: {sys.version}")
    print(f"Django版本: {django.get_version()}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"脚本执行路径: {os.path.abspath(__file__)}")
    
    # 检查matplotlib后端
    print(f"Matplotlib后端: {matplotlib.get_backend()}")
    
    print()

def check_django_settings():
    """检查Django设置"""
    print("🔍 Django设置检查")
    print("=" * 50)
    
    print(f"BASE_DIR: {settings.BASE_DIR}")
    print(f"MEDIA_ROOT: {getattr(settings, 'MEDIA_ROOT', '未设置')}")
    print(f"MEDIA_URL: {getattr(settings, 'MEDIA_URL', '未设置')}")
    print(f"STATIC_ROOT: {getattr(settings, 'STATIC_ROOT', '未设置')}")
    print(f"STATIC_URL: {getattr(settings, 'STATIC_URL', '未设置')}")
    print(f"DEBUG: {getattr(settings, 'DEBUG', False)}")
    print(f"ALLOWED_HOSTS: {getattr(settings, 'ALLOWED_HOSTS', [])}")
    
    print()

def check_directories():
    """检查目录状态"""
    print("🔍 目录状态检查")
    print("=" * 50)
    
    directories_to_check = [
        ('BASE_DIR', settings.BASE_DIR),
        ('MEDIA_ROOT', getattr(settings, 'MEDIA_ROOT', None)),
        ('BASE_DIR/images', os.path.join(settings.BASE_DIR, 'images')),
        ('/var/www/badminton-analysis/images', '/var/www/badminton-analysis/images'),
    ]
    
    for dir_name, dir_path in directories_to_check:
        if dir_path:
            print(f"\n📁 {dir_name}: {dir_path}")
            print(f"   存在: {os.path.exists(dir_path)}")
            print(f"   是目录: {os.path.isdir(dir_path) if os.path.exists(dir_path) else 'N/A'}")
            print(f"   可写: {os.access(dir_path, os.W_OK) if os.path.exists(dir_path) else 'N/A'}")
            print(f"   权限: {oct(os.stat(dir_path).st_mode)[-3:] if os.path.exists(dir_path) else 'N/A'}")
            
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                try:
                    files = os.listdir(dir_path)
                    image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
                    print(f"   总文件数: {len(files)}")
                    print(f"   图片文件数: {len(image_files)}")
                    if image_files:
                        print(f"   图片文件: {image_files}")
                except Exception as e:
                    print(f"   错误: {e}")
    
    print()

def test_image_generation():
    """测试图片生成"""
    print("🔍 图片生成测试")
    print("=" * 50)
    
    try:
        # 生成测试图片
        print("正在生成测试图片...")
        import math
        time_points = list(range(0, 1000, 10))
        test_sensor_data = {
            'waist': [abs(math.sin(t/100) * 2) for t in time_points],
            'shoulder': [abs(math.sin((t-50)/100) * 2.5) for t in time_points],
            'wrist': [abs(math.sin((t-100)/100) * 3) for t in time_points],
            'racket': [abs(math.sin((t-150)/100) * 3.5) for t in time_points]
        }
        
        result_path = generate_multi_sensor_curve(test_sensor_data, time_points, "debug_test_image.jpg")
        
        if result_path and os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"✅ 图片生成成功!")
            print(f"   文件路径: {result_path}")
            print(f"   文件大小: {file_size} bytes")
            print(f"   文件权限: {oct(os.stat(result_path).st_mode)[-3:]}")
            return True
        else:
            print(f"❌ 图片生成失败 - 文件不存在")
            return False
            
    except Exception as e:
        print(f"❌ 图片生成异常: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

def test_api_access():
    """测试API访问"""
    print("🔍 API访问测试")
    print("=" * 50)
    
    # 测试API端点
    api_endpoints = [
        'http://localhost:8000/api/debug_images/',
        'http://localhost:8000/api/list_images/',
        'http://localhost:8000/api/latest_analysis_images/',
        'http://127.0.0.1:8000/api/debug_images/',
    ]
    
    for endpoint in api_endpoints:
        try:
            print(f"\n📡 测试: {endpoint}")
            response = requests.get(endpoint, timeout=10)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   响应类型: JSON")
                    if 'debug_info' in data:
                        print(f"   包含调试信息: ✅")
                    if 'images' in data:
                        print(f"   包含图片信息: ✅")
                except:
                    print(f"   响应类型: 非JSON")
            else:
                print(f"   错误: {response.text[:200]}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ 连接失败 - 服务器可能未启动")
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")

def check_database_data():
    """检查数据库数据"""
    print("🔍 数据库数据检查")
    print("=" * 50)
    
    try:
        # 检查分析结果
        analysis_count = AnalysisResult.objects.count()
        print(f"分析结果总数: {analysis_count}")
        
        if analysis_count > 0:
            latest_analysis = AnalysisResult.objects.order_by('-analysis_time').first()
            print(f"最新分析ID: {latest_analysis.id}")
            print(f"最新分析时间: {latest_analysis.analysis_time}")
            print(f"关联会话ID: {latest_analysis.session_id}")
        
        # 检查会话数据
        session_count = DataCollectionSession.objects.count()
        print(f"数据采集会话总数: {session_count}")
        
        if session_count > 0:
            latest_session = DataCollectionSession.objects.order_by('-start_time').first()
            print(f"最新会话ID: {latest_session.id}")
            print(f"最新会话状态: {latest_session.status}")
            print(f"最新会话开始时间: {latest_session.start_time}")
        
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")
    
    print()

def generate_nginx_config():
    """生成Nginx配置建议"""
    print("🔍 Nginx配置建议")
    print("=" * 50)
    
    media_root = getattr(settings, 'MEDIA_ROOT', '/path/to/media')
    media_url = getattr(settings, 'MEDIA_URL', '/images/')
    
    nginx_config = f"""
# 添加到你的Nginx站点配置中
server {{
    listen 80;
    server_name your_domain.com;
    
    # 静态文件服务 - 图片访问
    location {media_url} {{
        alias {media_root}/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        
        # 允许跨域访问
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods GET;
        
        # 图片文件类型
        location ~* \\.(jpg|jpeg|png|gif|ico|svg)$ {{
            expires 1y;
            add_header Cache-Control "public, immutable";
        }}
    }}
    
    # Django应用
    location / {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
    
    print(nginx_config)
    
    # 保存配置到文件
    config_file = 'nginx_images_config.conf'
    with open(config_file, 'w') as f:
        f.write(nginx_config)
    print(f"\n配置已保存到: {config_file}")
    print()

def main():
    """主函数"""
    print(f"羽毛球分析系统 - 图片调试脚本")
    print(f"执行时间: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # 执行各项检查
    check_system_info()
    check_django_settings()
    check_directories()
    test_image_generation()
    check_database_data()
    test_api_access()
    generate_nginx_config()
    
    print("🎯 调试建议")
    print("=" * 50)
    print("1. 确保MEDIA_ROOT目录存在且可写")
    print("2. 检查Nginx配置是否正确处理静态文件")
    print("3. 确保Django服务正在运行")
    print("4. 检查防火墙设置是否允许访问")
    print("5. 验证图片生成后的文件权限")
    print("\n完成时间:", datetime.now().isoformat())

if __name__ == '__main__':
    main() 