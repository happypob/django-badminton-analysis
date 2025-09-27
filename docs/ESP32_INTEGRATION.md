# ESP32 硬件集成文档

## 📋 概述

本文档介绍如何将ESP32多传感器系统与羽毛球动作分析系统集成。

## 🔧 硬件要求

### ESP32开发板
- **型号**: ESP32-S3 或 ESP32-WROOM-32
- **Flash**: 最少 4MB，推荐 8MB+
- **RAM**: 最少 512KB
- **WiFi**: 支持802.11 b/g/n

### 传感器模块
- **IMU传感器**: MPU6050 或 MPU9250
- **数量**: 4个（腰部、肩部、腕部、球拍）
- **接口**: I2C
- **采样率**: 100Hz+

## 📁 固件文件

### 主要固件
- `esp32s3_multi_sensor_with_timer.ino` - 主固件（推荐）
- `esp32_multi_sensor_fixed.ino` - 兼容版本
- `esp32_wifi_notification_fixed.ino` - WiFi通知版本

### 固件选择指南

| 固件 | 适用场景 | 特点 |
|------|----------|------|
| esp32s3_multi_sensor_with_timer.ino | 生产环境 | 定时器驱动，稳定性好 |
| esp32_multi_sensor_fixed.ino | 兼容性测试 | 兼容老版本ESP32 |
| esp32_wifi_notification_fixed.ino | 网络环境 | 支持WiFi通知 |

## 🚀 快速开始

### 1. 环境准备

#### Arduino IDE设置
1. 安装Arduino IDE 2.0+
2. 安装ESP32开发板支持包
3. 安装必要的库：
   - `WiFi` (内置)
   - `HTTPClient` (内置)
   - `ArduinoJson` (6.x版本)
   - `MPU6050` (Adafruit版本)

#### 库安装
```bash
# 在Arduino IDE中安装以下库
- ArduinoJson by Benoit Blanchon
- Adafruit MPU6050 by Adafruit
- Adafruit Unified Sensor by Adafruit
```

### 2. 硬件连接

#### 传感器连接图
```
ESP32-S3    MPU6050
--------    -------
3.3V   -->  VCC
GND    -->  GND
GPIO21 -->  SDA
GPIO22 -->  SCL
```

#### 多传感器连接
```
传感器1 (腰部):   SDA=21, SCL=22, AD0=GND
传感器2 (肩部):   SDA=21, SCL=22, AD0=3.3V
传感器3 (腕部):   SDA=21, SCL=22, AD0=GPIO2
传感器4 (球拍):   SDA=21, SCL=22, AD0=GPIO4
```

### 3. 固件配置

#### WiFi配置
```cpp
const char* ssid = "YourWiFiSSID";
const char* password = "YourWiFiPassword";
```

#### 服务器配置
```cpp
const char* serverUrl = "http://your-server-ip:8000";
const char* deviceGroupCode = "badminton_group_001";
```

#### 传感器配置
```cpp
// 传感器地址配置
#define SENSOR_WAIST_ADDR   0x68  // AD0 = GND
#define SENSOR_SHOULDER_ADDR 0x69 // AD0 = 3.3V
#define SENSOR_WRIST_ADDR   0x6A  // AD0 = GPIO2
#define SENSOR_RACKET_ADDR  0x6B  // AD0 = GPIO4
```

## 📡 通信协议

### 1. 数据格式

#### 传感器数据结构
```json
{
  "device_code": "waist_sensor_001",
  "sensor_type": "waist",
  "data": {
    "acc": [1.2, 0.8, 9.8],
    "gyro": [0.1, 0.2, 0.3],
    "angle": [45.0, 30.0, 60.0],
    "timestamp": 1640995200000
  }
}
```

#### 批量上传格式
```json
{
  "device_group_code": "badminton_group_001",
  "session_id": 123,
  "sensors": [
    {
      "device_code": "waist_sensor_001",
      "sensor_type": "waist",
      "data": [...]
    },
    {
      "device_code": "shoulder_sensor_001", 
      "sensor_type": "shoulder",
      "data": [...]
    }
  ]
}
```

### 2. API接口

#### 数据上传接口
```
POST /wxapp/upload_sensor_data/
```

**请求参数**:
- `device_group_code`: 设备组编码
- `session_id`: 会话ID（可选）
- `sensors`: 传感器数据数组

#### 状态查询接口
```
GET /wxapp/get_device_status/
```

**请求参数**:
- `device_group_code`: 设备组编码

**响应**:
```json
{
  "status": "calibrating",
  "session_id": 123,
  "command": "CALIBRATE_badminton_group_001"
}
```

## 🔄 工作流程

### 1. 初始化流程
```
ESP32启动 → 连接WiFi → 初始化传感器 → 等待服务器命令
```

### 2. 数据采集流程
```
接收开始命令 → 开始数据采集 → 存储到SD卡 → 接收结束命令 → 上传数据
```

### 3. 校准流程
```
接收校准命令 → 执行校准程序 → 发送校准完成状态 → 等待采集命令
```

## ⚙️ 高级配置

### 1. 采样率配置
```cpp
// 设置采样率为100Hz
#define SAMPLE_RATE 100
#define SAMPLE_INTERVAL 1000/SAMPLE_RATE  // 10ms
```

### 2. 数据存储配置
```cpp
// SD卡配置
#define SD_CS_PIN 5
#define SD_MOSI_PIN 23
#define SD_MISO_PIN 19
#define SD_SCK_PIN 18
```

### 3. 电源管理
```cpp
// 低功耗模式配置
#define LOW_POWER_MODE true
#define SLEEP_DURATION 60000  // 60秒
```

## 🐛 故障排除

### 常见问题

1. **传感器初始化失败**
   - 检查I2C连接
   - 确认传感器地址
   - 检查电源供应

2. **WiFi连接失败**
   - 检查SSID和密码
   - 确认信号强度
   - 检查路由器设置

3. **数据上传失败**
   - 检查服务器地址
   - 确认网络连接
   - 查看服务器日志

4. **SD卡写入失败**
   - 检查SD卡格式
   - 确认SD卡容量
   - 检查连接线路

### 调试工具

#### 串口调试
```cpp
// 启用串口调试
#define DEBUG_SERIAL true
#define DEBUG_BAUD 115200
```

#### 网络调试
```cpp
// 启用网络调试
#define DEBUG_HTTP true
#define DEBUG_URL "http://your-server:8000/debug/"
```

## 📊 性能优化

### 1. 数据压缩
```cpp
// 启用数据压缩
#define ENABLE_COMPRESSION true
#define COMPRESSION_LEVEL 6
```

### 2. 批量上传
```cpp
// 批量上传配置
#define BATCH_SIZE 50
#define UPLOAD_INTERVAL 5000  // 5秒
```

### 3. 缓存管理
```cpp
// 内存缓存配置
#define CACHE_SIZE 1000
#define CACHE_THRESHOLD 800
```

## 🔧 维护指南

### 1. 固件更新
```bash
# 通过Arduino IDE更新固件
1. 打开对应的.ino文件
2. 修改配置参数
3. 编译并上传到ESP32
```

### 2. 配置更新
```cpp
// 通过Web界面更新配置
http://esp32-ip/config
```

### 3. 数据备份
```bash
# 备份SD卡数据
sudo dd if=/dev/sdb of=backup.img bs=4M
```

## 📞 技术支持

### 日志收集
```cpp
// 启用详细日志
#define LOG_LEVEL 3  // 0=ERROR, 1=WARN, 2=INFO, 3=DEBUG
```

### 错误报告
报告问题时请提供：
1. 固件版本
2. 硬件配置
3. 错误日志
4. 复现步骤

### 联系方式
- 技术文档: [项目Wiki]
- 问题反馈: [GitHub Issues]
- 邮件支持: support@example.com
