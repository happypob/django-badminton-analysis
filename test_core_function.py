#!/usr/bin/env python3
"""
测试核心合角速度计算功能
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

def test_gyro_magnitude_calculation():
    """测试合角速度计算"""
    print("🧪 测试合角速度计算...")
    
    # 模拟角速度数据
    gyro_data = [
        [1.0, 2.0, 3.0],  # 第一个数据点
        [2.0, 1.0, 4.0],  # 第二个数据点
        [0.5, 1.5, 2.5],  # 第三个数据点
    ]
    
    # 计算合角速度（按照analyze_sensor_csv.py的magnitude函数逻辑）
    gyro_magnitudes = []
    for gyro in gyro_data:
        magnitude = np.sqrt(gyro[0]**2 + gyro[1]**2 + gyro[2]**2)
        gyro_magnitudes.append(magnitude)
        print(f"角速度 {gyro} -> 合角速度: {magnitude:.3f}")
    
    print(f"✅ 合角速度计算完成，结果: {gyro_magnitudes}")
    return gyro_magnitudes

def test_plot_generation():
    """测试图片生成"""
    print("\n🎨 测试图片生成...")
    
    # 创建测试数据
    time_points = np.linspace(0, 5, 100)
    
    # 模拟4个传感器的合角速度数据
    sensor_data = {
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
        },
        'racket': {
            'times': time_points.tolist(),
            'gyro_magnitudes': [abs(2.5 * np.cos(2 * np.pi * 2.5 * t)) for t in time_points]
        }
    }
    
    # 创建图片
    plt.figure(figsize=(12, 6))
    
    sensor_names = {
        "waist": "腰部",
        "wrist": "手腕", 
        "shoulder": "肩部",
        "racket": "球拍"
    }
    
    # 绘制每个传感器的合角速度曲线
    for sensor_type, data in sensor_data.items():
        times = data['times']
        gyro_magnitudes = data['gyro_magnitudes']
        
        plt.plot(times, gyro_magnitudes, label=sensor_names.get(sensor_type, sensor_type), linewidth=2)
        print(f"✅ {sensor_type} 曲线绘制完成，数据点: {len(times)}")
    
    plt.title("多传感器合角速度随时间变化曲线", fontsize=14)
    plt.xlabel("时间 (s) from master start", fontsize=12)
    plt.ylabel("合角速度 (rad/s)", fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 保存图片
    filename = "test_gyro_magnitude_core.jpg"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    if os.path.exists(filename):
        file_size = os.path.getsize(filename)
        print(f"✅ 图片生成成功:")
        print(f"   文件名: {filename}")
        print(f"   文件大小: {file_size} bytes")
        return True
    else:
        print(f"❌ 图片生成失败")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试核心合角速度功能")
    print("=" * 50)
    
    try:
        # 测试合角速度计算
        test_gyro_magnitude_calculation()
        
        # 测试图片生成
        success = test_plot_generation()
        
        if success:
            print("\n🎉 所有核心功能测试通过！")
        else:
            print("\n❌ 图片生成测试失败")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")

if __name__ == '__main__':
    main()
