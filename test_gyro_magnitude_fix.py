#!/usr/bin/env python3
"""
测试修正后的合角速度图片生成功能
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

from wxapp.models import DataCollectionSession, SensorData, AnalysisResult
from wxapp.views import extract_angular_velocity_data, generate_multi_sensor_curve
from django.utils import timezone

def create_test_session():
    """创建测试会话和传感器数据"""
    print("🔧 创建测试会话...")
    
    # 创建测试会话
    session = DataCollectionSession.objects.create(
        wx_user_id="test_user_gyro_fix",
        status='completed',
        start_time=timezone.now() - timedelta(minutes=5),
        end_time=timezone.now()
    )
    
    print(f"✅ 创建会话: {session.id}")
    
    # 创建测试传感器数据
    sensor_types = ['waist', 'shoulder', 'wrist', 'racket']
    base_time = timezone.now() - timedelta(minutes=5)
    
    for i, sensor_type in enumerate(sensor_types):
        print(f"📊 创建 {sensor_type} 传感器数据...")
        
        # 生成模拟的角速度数据
        time_points = np.linspace(0, 5, 100)  # 5秒，100个数据点
        frequency = 1.0 + i * 0.5  # 不同传感器不同频率
        
        for j, t in enumerate(time_points):
            # 生成模拟的角速度数据 (rad/s)
            gyro_x = 2.0 * np.sin(2 * np.pi * frequency * t) + 0.1 * np.random.randn()
            gyro_y = 1.5 * np.cos(2 * np.pi * frequency * t) + 0.1 * np.random.randn()
            gyro_z = 1.0 * np.sin(2 * np.pi * frequency * t + np.pi/4) + 0.1 * np.random.randn()
            
            # 创建传感器数据
            data_dict = {
                'acc': [0.0, 0.0, 9.8],  # 重力加速度
                'gyro': [float(gyro_x), float(gyro_y), float(gyro_z)],
                'angle': [0.0, 0.0, 0.0],
                'timestamp': int(t * 1000)  # 毫秒时间戳
            }
            
            SensorData.objects.create(
                session=session,
                device_code=f"test_device_{sensor_type}",
                sensor_type=sensor_type,
                data=json.dumps(data_dict),
                timestamp=base_time + timedelta(seconds=t),
                esp32_timestamp=base_time + timedelta(seconds=t)
            )
    
    print(f"✅ 创建了 {SensorData.objects.filter(session=session).count()} 条传感器数据")
    return session

def test_extract_angular_velocity_data(session):
    """测试角速度数据提取功能"""
    print("\n🔍 测试角速度数据提取...")
    
    angle_data = extract_angular_velocity_data(session)
    
    print(f"📊 提取结果:")
    print(f"   传感器组数量: {len(angle_data['sensor_groups'])}")
    print(f"   主时间窗口: {angle_data.get('master_start', 'N/A'):.3f} - {angle_data.get('master_end', 'N/A'):.3f} 秒")
    
    for sensor_type, sensor_data in angle_data['sensor_groups'].items():
        times = sensor_data['times']
        gyro_magnitudes = sensor_data['gyro_magnitudes']
        print(f"   {sensor_type}: {len(times)} 个数据点")
        if times and gyro_magnitudes:
            print(f"     时间范围: {min(times):.3f} - {max(times):.3f} 秒")
            print(f"     角速度范围: {min(gyro_magnitudes):.3f} - {max(gyro_magnitudes):.3f} rad/s")
    
    return angle_data

def test_generate_multi_sensor_curve(angle_data, session):
    """测试合角速度图片生成功能"""
    print("\n🎨 测试合角速度图片生成...")
    
    filename = f"test_gyro_fix_session_{session.id}.jpg"
    result_path = generate_multi_sensor_curve(angle_data, None, filename)
    
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
    print("\n🧪 测试不同传感器数量情况...")
    
    # 测试只有1个传感器
    print("\n📊 测试1个传感器...")
    session1 = create_test_session()
    # 删除其他传感器数据，只保留waist
    SensorData.objects.filter(session=session1).exclude(sensor_type='waist').delete()
    
    angle_data1 = extract_angular_velocity_data(session1)
    if angle_data1['sensor_groups']:
        test_generate_multi_sensor_curve(angle_data1, session1)
    
    # 测试2个传感器
    print("\n📊 测试2个传感器...")
    session2 = create_test_session()
    # 删除其他传感器数据，只保留waist和shoulder
    SensorData.objects.filter(session=session2).exclude(sensor_type__in=['waist', 'shoulder']).delete()
    
    angle_data2 = extract_angular_velocity_data(session2)
    if angle_data2['sensor_groups']:
        test_generate_multi_sensor_curve(angle_data2, session2)
    
    # 测试3个传感器
    print("\n📊 测试3个传感器...")
    session3 = create_test_session()
    # 删除其他传感器数据，只保留waist、shoulder和wrist
    SensorData.objects.filter(session=session3).exclude(sensor_type__in=['waist', 'shoulder', 'wrist']).delete()
    
    angle_data3 = extract_angular_velocity_data(session3)
    if angle_data3['sensor_groups']:
        test_generate_multi_sensor_curve(angle_data3, session3)
    
    # 测试4个传感器（全部）
    print("\n📊 测试4个传感器...")
    session4 = create_test_session()
    angle_data4 = extract_angular_velocity_data(session4)
    if angle_data4['sensor_groups']:
        test_generate_multi_sensor_curve(angle_data4, session4)

def cleanup_test_data():
    """清理测试数据"""
    print("\n🧹 清理测试数据...")
    
    # 删除测试会话和相关数据
    test_sessions = DataCollectionSession.objects.filter(wx_user_id="test_user_gyro_fix")
    for session in test_sessions:
        SensorData.objects.filter(session=session).delete()
        AnalysisResult.objects.filter(session=session).delete()
        session.delete()
    
    print(f"✅ 清理完成，删除了 {test_sessions.count()} 个测试会话")

def main():
    """主测试函数"""
    print("🚀 开始测试修正后的合角速度图片生成功能")
    print("=" * 60)
    
    try:
        # 测试基本功能
        session = create_test_session()
        angle_data = test_extract_angular_velocity_data(session)
        success = test_generate_multi_sensor_curve(angle_data, session)
        
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
    
    finally:
        # 清理测试数据
        cleanup_test_data()

if __name__ == '__main__':
    main()
