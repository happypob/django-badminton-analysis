#!/usr/bin/env python3
"""
简化的合角速度图片生成测试
"""

import os
import sys
import django
import json
import numpy as np
from datetime import datetime, timedelta

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangodemo.settings')
django.setup()

from wxapp.models import DataCollectionSession, SensorData
from wxapp.views import extract_angular_velocity_data, generate_multi_sensor_curve
from django.utils import timezone

def test_with_mock_data():
    """使用模拟数据测试功能"""
    print("🧪 使用模拟数据测试合角速度图片生成...")
    
    # 创建模拟的sensor_groups数据
    time_points = np.linspace(0, 5, 100)  # 5秒，100个数据点
    
    mock_angle_data = {
        'sensor_groups': {
            'waist': {
                'times': time_points.tolist(),
                'gyro_magnitudes': [abs(2.0 * np.sin(2 * np.pi * 1.0 * t) + 0.1 * np.random.randn()) for t in time_points]
            },
            'shoulder': {
                'times': time_points.tolist(),
                'gyro_magnitudes': [abs(1.5 * np.cos(2 * np.pi * 1.5 * t) + 0.1 * np.random.randn()) for t in time_points]
            },
            'wrist': {
                'times': time_points.tolist(),
                'gyro_magnitudes': [abs(1.0 * np.sin(2 * np.pi * 2.0 * t + np.pi/4) + 0.1 * np.random.randn()) for t in time_points]
            },
            'racket': {
                'times': time_points.tolist(),
                'gyro_magnitudes': [abs(2.5 * np.cos(2 * np.pi * 2.5 * t + np.pi/2) + 0.1 * np.random.randn()) for t in time_points]
            }
        },
        'master_start': 0,
        'master_end': 5.0
    }
    
    print(f"📊 模拟数据统计:")
    print(f"   传感器数量: {len(mock_angle_data['sensor_groups'])}")
    print(f"   时间范围: {mock_angle_data['master_start']} - {mock_angle_data['master_end']} 秒")
    
    for sensor_type, sensor_data in mock_angle_data['sensor_groups'].items():
        times = sensor_data['times']
        gyro_magnitudes = sensor_data['gyro_magnitudes']
        print(f"   {sensor_type}: {len(times)} 个数据点")
        print(f"     角速度范围: {min(gyro_magnitudes):.3f} - {max(gyro_magnitudes):.3f} rad/s")
    
    # 测试图片生成
    print("\n🎨 测试图片生成...")
    filename = "test_gyro_magnitude_fix.jpg"
    result_path = generate_multi_sensor_curve(mock_angle_data, None, filename)
    
    if result_path and os.path.exists(result_path):
        file_size = os.path.getsize(result_path)
        print(f"✅ 图片生成成功:")
        print(f"   文件路径: {result_path}")
        print(f"   文件大小: {file_size} bytes")
        return True
    else:
        print(f"❌ 图片生成失败")
        return False

def test_different_sensor_counts():
    """测试不同传感器数量的情况"""
    print("\n🧪 测试不同传感器数量...")
    
    time_points = np.linspace(0, 3, 60)  # 3秒，60个数据点
    
    # 测试1个传感器
    print("\n📊 测试1个传感器...")
    mock_data_1 = {
        'sensor_groups': {
            'waist': {
                'times': time_points.tolist(),
                'gyro_magnitudes': [abs(2.0 * np.sin(2 * np.pi * 1.0 * t)) for t in time_points]
            }
        },
        'master_start': 0,
        'master_end': 3.0
    }
    
    filename_1 = "test_1_sensor.jpg"
    result_1 = generate_multi_sensor_curve(mock_data_1, None, filename_1)
    print(f"1个传感器: {'✅ 成功' if result_1 else '❌ 失败'}")
    
    # 测试2个传感器
    print("\n📊 测试2个传感器...")
    mock_data_2 = {
        'sensor_groups': {
            'waist': {
                'times': time_points.tolist(),
                'gyro_magnitudes': [abs(2.0 * np.sin(2 * np.pi * 1.0 * t)) for t in time_points]
            },
            'shoulder': {
                'times': time_points.tolist(),
                'gyro_magnitudes': [abs(1.5 * np.cos(2 * np.pi * 1.5 * t)) for t in time_points]
            }
        },
        'master_start': 0,
        'master_end': 3.0
    }
    
    filename_2 = "test_2_sensors.jpg"
    result_2 = generate_multi_sensor_curve(mock_data_2, None, filename_2)
    print(f"2个传感器: {'✅ 成功' if result_2 else '❌ 失败'}")
    
    # 测试3个传感器
    print("\n📊 测试3个传感器...")
    mock_data_3 = {
        'sensor_groups': {
            'waist': {
                'times': time_points.tolist(),
                'gyro_magnitudes': [abs(2.0 * np.sin(2 * np.pi * 1.0 * t)) for t in time_points]
            },
            'shoulder': {
                'times': time_points.tolist(),
                'gyro_magnitudes': [abs(1.5 * np.cos(2 * np.pi * 1.5 * t)) for t in time_points]
            },
            'wrist': {
                'times': time_points.tolist(),
                'gyro_magnitudes': [abs(1.0 * np.sin(2 * np.pi * 2.0 * t)) for t in time_points]
            }
        },
        'master_start': 0,
        'master_end': 3.0
    }
    
    filename_3 = "test_3_sensors.jpg"
    result_3 = generate_multi_sensor_curve(mock_data_3, None, filename_3)
    print(f"3个传感器: {'✅ 成功' if result_3 else '❌ 失败'}")

def main():
    """主测试函数"""
    print("🚀 开始测试修正后的合角速度图片生成功能")
    print("=" * 60)
    
    try:
        # 测试基本功能
        success = test_with_mock_data()
        
        if success:
            print("\n✅ 基本功能测试通过")
        else:
            print("\n❌ 基本功能测试失败")
            return
        
        # 测试不同传感器数量
        test_different_sensor_counts()
        
        print("\n🎉 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")

if __name__ == '__main__':
    main()
