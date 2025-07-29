import os
import django
import numpy as np
from scipy.io import savemat

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangodemo.settings')
django.setup()

from wxapp.models import WxUser, SensorData, DataCollectionSession, DeviceGroup
from wxapp.views import process_mat_data

def create_test_mat_file():
    """创建测试用的.mat文件"""
    
    # 创建模拟数据
    # 格式: [设备ID, 时间戳, 加速度XYZ, 角速度XYZ, 角度XYZ]
    num_samples = 100
    
    # 腰部传感器数据 (ID=1)
    waist_data = []
    for i in range(num_samples):
        row = [
            1,  # 设备ID - 腰部
            i * 0.01,  # 时间戳
            *np.random.randn(3),  # 加速度XYZ
            *np.random.randn(3),  # 角速度XYZ
            *np.random.randn(3),  # 角度XYZ
        ]
        waist_data.append(row)
    
    # 肩部传感器数据 (ID=2)
    shoulder_data = []
    for i in range(num_samples):
        row = [
            2,  # 设备ID - 肩部
            i * 0.01,  # 时间戳
            *np.random.randn(3),  # 加速度XYZ
            *np.random.randn(3),  # 角速度XYZ
            *np.random.randn(3),  # 角度XYZ
        ]
        shoulder_data.append(row)
    
    # 腕部传感器数据 (ID=4)
    wrist_data = []
    for i in range(num_samples):
        row = [
            4,  # 设备ID - 腕部
            i * 0.01,  # 时间戳
            *np.random.randn(3),  # 加速度XYZ
            *np.random.randn(3),  # 角速度XYZ
            *np.random.randn(3),  # 角度XYZ
        ]
        wrist_data.append(row)
    
    # 合并所有数据
    all_data = np.array(waist_data + shoulder_data + wrist_data)
    
    # 保存为.mat文件
    mat_data = {'allData': all_data}
    savemat('test_sensor_data.mat', mat_data)
    
    print("测试.mat文件已创建: test_sensor_data.mat")
    print(f"数据形状: {all_data.shape}")
    print(f"腰部数据: {len(waist_data)} 条")
    print(f"肩部数据: {len(shoulder_data)} 条")
    print(f"腕部数据: {len(wrist_data)} 条")

def test_sensor_id_consistency():
    """测试传感器ID的一致性"""
    
    # 获取或创建测试用户
    wx_user, created = WxUser.objects.get_or_create(
        openid='test_sensor_id_user',
        defaults={'user_id': 9999}
    )
    
    # 加载测试.mat文件
    from scipy.io import loadmat
    mat_data = loadmat('test_sensor_data.mat')
    
    # 处理数据
    session_data = process_mat_data(mat_data, wx_user)
    session_id = session_data['session_id']
    
    print(f"\n会话ID: {session_id}")
    print(f"数据摘要: {session_data['summary']}")
    
    # 检查传感器数据
    session = DataCollectionSession.objects.get(id=session_id)
    sensor_data = SensorData.objects.filter(session=session)
    
    print(f"\n传感器数据统计:")
    print(f"总记录数: {sensor_data.count()}")
    
    # 按传感器类型分组
    sensor_types = {}
    device_codes = {}
    
    for data in sensor_data:
        sensor_type = data.sensor_type
        device_code = data.device_code
        
        if sensor_type not in sensor_types:
            sensor_types[sensor_type] = 0
        sensor_types[sensor_type] += 1
        
        if device_code not in device_codes:
            device_codes[device_code] = 0
        device_codes[device_code] += 1
    
    print(f"\n传感器类型分布:")
    for sensor_type, count in sensor_types.items():
        print(f"  {sensor_type}: {count} 条记录")
    
    print(f"\n设备编码分布:")
    for device_code, count in device_codes.items():
        print(f"  {device_code}: {count} 条记录")
    
    # 验证传感器ID是否固定
    expected_device_codes = {
        'waist': 'waist_sensor_001',
        'shoulder': 'shoulder_sensor_001', 
        'wrist': 'wrist_sensor_001'
    }
    
    print(f"\n传感器ID一致性检查:")
    for sensor_type, expected_code in expected_device_codes.items():
        actual_code = None
        for data in sensor_data.filter(sensor_type=sensor_type):
            actual_code = data.device_code
            break
        
        if actual_code == expected_code:
            print(f"  ✓ {sensor_type}: {actual_code}")
        else:
            print(f"  ✗ {sensor_type}: 期望 {expected_code}, 实际 {actual_code}")

if __name__ == '__main__':
    print("开始测试传感器ID修复...")
    
    # 创建测试文件
    create_test_mat_file()
    
    # 测试传感器ID一致性
    test_sensor_id_consistency()
    
    print("\n测试完成！") 