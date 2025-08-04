# ESP32-S3 羽毛球传感器系统 API 测试指南

## 📋 系统概述

本系统包含ESP32-S3设备、Django后端服务器和小程序前端，实现羽毛球运动数据的采集、传输和分析。

### 设备配置
- **设备码**: 2025001
- **服务器地址**: http://47.122.129.159:8000
- **WiFi配置**: SSID="111", Password="12345678"

## 🔧 ESP32 代码文件

### 1. 完整版本 (`esp32_wifi_notification_fixed.ino`)
- 包含Web服务器功能
- 支持远程控制开始/停止采集
- 支持设备状态查询
- 适合生产环境使用

### 2. 简化测试版本 (`esp32_simple_test.ino`)
- 自动上传测试数据
- 使用固定会话ID (1011)
- 适合快速测试和调试

## 📡 API 接口列表

### 1. ESP32数据上传接口
```
POST /wxapp/esp32/upload/
```

**参数:**
- `device_code`: 设备码 (如: 2025001)
- `sensor_type`: 传感器类型 (waist/shoulder/wrist)
- `data`: JSON格式的传感器数据
- `session_id`: 会话ID
- `timestamp`: 时间戳

**测试命令:**
```bash
curl -X POST http://47.122.129.159:8000/wxapp/esp32/upload/ \
  -d "device_code=2025001" \
  -d "sensor_type=waist" \
  -d "data={\"acc\":[1.2,0.8,9.8],\"gyro\":[0.1,0.2,0.3],\"angle\":[45.0,30.0,60.0]}" \
  -d "session_id=1011" \
  -d "timestamp=1234567890"
```

### 2. 设备IP注册接口
```
POST /wxapp/register_device_ip/
```

**参数:**
- `device_code`: 设备码
- `ip_address`: 设备IP地址

**测试命令:**
```bash
curl -X POST http://47.122.129.159:8000/wxapp/register_device_ip/ \
  -d "device_code=2025001" \
  -d "ip_address=192.168.1.100"
```

### 3. 开始数据采集接口
```
POST /wxapp/start_collection/
```

**参数:**
- `device_code`: 设备码
- `session_id`: 会话ID

**测试命令:**
```bash
curl -X POST http://47.122.129.159:8000/wxapp/start_collection/ \
  -d "device_code=2025001" \
  -d "session_id=1011"
```

### 4. 停止数据采集接口
```
POST /wxapp/stop_collection/
```

**参数:**
- `device_code`: 设备码

**测试命令:**
```bash
curl -X POST http://47.122.129.159:8000/wxapp/stop_collection/ \
  -d "device_code=2025001"
```

### 5. 设备状态查询接口
```
GET /wxapp/device_status/
```

**参数:**
- `device_code`: 设备码

**测试命令:**
```bash
curl -X GET "http://47.122.129.159:8000/wxapp/device_status/?device_code=2025001"
```

## 🧪 测试步骤

### 步骤1: 创建测试会话
在Django shell中创建测试会话：
```python
from wxapp.models import DataCollectionSession, User, WxUser, DeviceGroup
from django.utils import timezone

# 创建测试用户
user, created = User.objects.get_or_create(
    username="test_user",
    defaults={"email": "test@example.com"}
)

# 创建WxUser
wx_user, created = WxUser.objects.get_or_create(
    openid="test_user_123",
    defaults={"user": user}
)

# 创建设备组
device_group, created = DeviceGroup.objects.get_or_create(
    group_code="test_group_001"
)

# 创建测试会话
session = DataCollectionSession.objects.create(
    device_group=device_group,
    user=wx_user,
    start_time=timezone.now(),
    status="collecting"
)
print(f"Created session with ID: {session.id}")
```

### 步骤2: 测试数据上传
使用创建的会话ID测试数据上传：
```bash
curl -X POST http://47.122.129.159:8000/wxapp/esp32/upload/ \
  -d "device_code=2025001" \
  -d "sensor_type=waist" \
  -d "data={\"acc\":[1.2,0.8,9.8],\"gyro\":[0.1,0.2,0.3],\"angle\":[45.0,30.0,60.0]}" \
  -d "session_id=1011" \
  -d "timestamp=1234567890"
```

### 步骤3: 上传ESP32代码
1. 打开Arduino IDE
2. 选择ESP32-S3开发板
3. 上传 `esp32_simple_test.ino` 或 `esp32_wifi_notification_fixed.ino`
4. 打开串口监视器查看输出

## 📊 预期输出

### 成功的数据上传响应
```json
{
  "msg": "ESP32 data upload success",
  "data_id": 1602,
  "device_code": "2025001",
  "sensor_type": "waist",
  "timestamp": "2025-08-04T11:21:28.997067+00:00",
  "sensor_data_summary": {
    "acc_magnitude": 9.91,
    "gyro_magnitude": 0.37,
    "angle_range": {
      "x": 45.0,
      "y": 30.0,
      "z": 60.0
    }
  },
  "session_id": 1011,
  "session_status": "collecting",
  "session_stats": {
    "total_data_points": 1,
    "active_sensor_types": 1
  }
}
```

### ESP32串口输出示例
```
🚀 ESP32-S3 简单测试程序
========================================
设备码: 2025001
服务器: http://47.122.129.159:8000
测试会话ID: 1011
========================================
🔄 连接WiFi...
连接中... 1/20
连接中... 2/20
✅ WiFi连接成功!
IP地址: 192.168.1.100
信号强度: -45 dBm
✅ 系统初始化完成，开始自动上传测试数据
📤 开始自动上传测试数据
📡 上传 waist 数据 (第1次)...
✅ waist 上传成功 (HTTP: 200)
🎉 waist 数据上传成功确认
```

## 🔍 故障排除

### 常见问题

1. **WiFi连接失败**
   - 检查WiFi名称和密码
   - 确保ESP32在WiFi覆盖范围内

2. **数据上传失败**
   - 检查服务器地址是否正确
   - 确认会话ID存在且有效
   - 检查网络连接

3. **编译错误**
   - 确保选择了正确的开发板 (ESP32-S3)
   - 检查库文件是否正确安装

4. **服务器404错误**
   - 确认Django服务器正在运行
   - 检查URL路径是否正确

### 调试命令

查看服务器日志：
```bash
tail -f django.log
```

检查Django进程：
```bash
ps aux | grep "python manage.py runserver"
```

重启Django服务器：
```bash
pkill -f "python manage.py runserver"
nohup python manage.py runserver 0.0.0.0:8000 > django.log 2>&1 &
```

## 📈 性能监控

### 数据上传频率
- 每个传感器类型间隔: 2-3秒
- 完整循环时间: 6-9秒
- 预期每小时上传: 1200-1800个数据点

### 系统资源
- ESP32内存使用: ~8KB (FreeRTOS任务)
- 网络带宽: ~1KB/次上传
- 服务器存储: ~100字节/数据点

## 🎯 下一步计划

1. **集成真实传感器**
   - 连接MPU6050/MPU9250传感器
   - 实现实时数据采集

2. **优化数据传输**
   - 实现数据压缩
   - 添加断线重连机制

3. **数据分析功能**
   - 实现运动轨迹分析
   - 添加击球动作识别

4. **小程序集成**
   - 实现设备绑定
   - 添加实时数据展示 