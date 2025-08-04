# ESP32 SD卡数据上传API指南

## 概述

新的工作流程采用SD卡存储 + 一次性上传的方式，避免网络传输的实时性问题。

## 工作流程

### 1. 开始采集
**小程序端** → **后台API** → **ESP32**

```
POST /wxapp/start_session/
{
    "openid": "用户openid",
    "device_group_code": "设备组代码"
}

响应:
{
    "msg": "session started",
    "session_id": 1011,
    "status": "calibrating"
}
```

### 2. 开始数据采集
**小程序端** → **后台API** → **ESP32**

```
POST /wxapp/start_data_collection/
{
    "session_id": 1011
}

响应:
{
    "msg": "Data collection started",
    "session_id": 1011,
    "status": "collecting"
}
```

### 3. 结束采集
**小程序端** → **后台API** → **ESP32**

```
POST /wxapp/end_session/
{
    "session_id": 1011
}

响应:
{
    "msg": "session ended",
    "session_id": 1011,
    "status": "stopped"
}
```

### 4. ESP32数据上传
**ESP32** → **后台API**

#### 4.1 批量上传传感器数据
```
POST /wxapp/esp32/batch_upload/
{
    "device_code": "2025001",
    "sensor_type": "waist",
    "session_id": 1011,
    "batch_data": [
        {
            "acc": [1.2, 2.3, 9.8],
            "gyro": [0.1, 0.2, 0.3],
            "angle": [45.0, 30.0, 60.0]
        },
        {
            "acc": [1.3, 2.4, 9.9],
            "gyro": [0.2, 0.3, 0.4],
            "angle": [46.0, 31.0, 61.0]
        }
    ]
}

响应:
{
    "msg": "Batch upload completed",
    "total_items": 2,
    "successful_items": 2,
    "failed_items": 0,
    "results": [...]
}
```

#### 4.2 标记上传完成
```
POST /wxapp/esp32/mark_upload_complete/
{
    "session_id": 1011,
    "device_code": "2025001",
    "upload_stats": "{\"total_files\": 3, \"total_bytes\": 1024000, \"upload_time_ms\": 5000}"
}

响应:
{
    "msg": "ESP32 data upload completed and analysis triggered",
    "session_id": 1011,
    "device_code": "2025001",
    "session_status": "analyzing",
    "data_collection_stats": {
        "total_data_points": 1500,
        "sensor_types": ["waist", "shoulder", "wrist"],
        "collection_duration_seconds": 30.5
    },
    "upload_stats": {...},
    "analysis_triggered": true,
    "analysis_id": 456,
    "analysis_status": "completed"
}
```

## API接口详细说明

### 1. 会话管理接口

#### 1.1 开始采集会话
- **URL**: `/wxapp/start_session/`
- **方法**: POST
- **参数**:
  - `openid`: 用户openid
  - `device_group_code`: 设备组代码
- **响应**: 返回会话ID和状态

#### 1.2 开始数据采集
- **URL**: `/wxapp/start_data_collection/`
- **方法**: POST
- **参数**:
  - `session_id`: 会话ID
- **功能**: 将会话状态从`calibrating`变为`collecting`

#### 1.3 结束采集会话
- **URL**: `/wxapp/end_session/`
- **方法**: POST
- **参数**:
  - `session_id`: 会话ID
- **功能**: 结束会话并触发分析

### 2. ESP32专用接口

#### 2.1 批量数据上传
- **URL**: `/wxapp/esp32/batch_upload/`
- **方法**: POST
- **参数**:
  - `device_code`: 设备码 (如: "2025001")
  - `sensor_type`: 传感器类型 ("waist", "shoulder", "wrist", "racket")
  - `session_id`: 会话ID
  - `batch_data`: JSON数组格式的传感器数据
- **功能**: 批量上传传感器数据

#### 2.2 标记上传完成
- **URL**: `/wxapp/esp32/mark_upload_complete/`
- **方法**: POST
- **参数**:
  - `session_id`: 会话ID
  - `device_code`: 设备码
  - `upload_stats`: 上传统计信息JSON (可选)
- **功能**: 标记数据上传完成并触发分析

#### 2.3 设备状态检查
- **URL**: `/wxapp/esp32/status/`
- **方法**: GET
- **功能**: 检查ESP32设备状态

## 设备码规范

- **统一设备码**: `2025001`
- **传感器类型映射**:
  - 1 → "waist" (腰部)
  - 2 → "shoulder" (肩部)
  - 3 → "wrist" (腕部)
  - 4 → "racket" (球拍)

## 会话状态说明

- `calibrating`: 校准状态
- `collecting`: 数据采集状态
- `analyzing`: 数据分析状态
- `completed`: 分析完成状态
- `stopped`: 已停止状态

## 错误处理

### 常见错误码
- `400`: 参数错误
- `404`: 会话不存在
- `500`: 服务器内部错误

### 错误响应格式
```json
{
    "error": "错误描述",
    "session_id": 1011,
    "current_status": "collecting"
}
```

## 测试工具

### 1. 测试脚本
```bash
# 测试ESP32上传完成接口
python test_esp32_upload_complete.py

# 测试批量上传
python test_multi_sensor.py

# 检查会话状态
python check_session.py
```

### 2. 手动测试
```bash
# 测试API文档
curl -X GET "http://47.122.129.159:8000/wxapp/esp32/mark_upload_complete/"

# 测试上传完成
curl -X POST "http://47.122.129.159:8000/wxapp/esp32/mark_upload_complete/" \
  -d "session_id=1011&device_code=2025001&upload_stats={\"total_files\":3}"
```

## 注意事项

1. **设备码统一**: 所有ESP32设备都使用设备码 `2025001`
2. **会话状态**: 确保会话在`collecting`或`calibrating`状态才能上传数据
3. **数据格式**: 传感器数据必须是有效的JSON格式
4. **错误处理**: ESP32应该处理网络错误和重试机制
5. **上传统计**: 建议ESP32提供上传统计信息以便调试

## 部署检查清单

- [ ] 后台API已部署到服务器
- [ ] 所有URL路由已配置
- [ ] 数据库模型支持新的字段
- [ ] 测试脚本可以正常运行
- [ ] ESP32代码已更新设备码为 `2025001`
- [ ] 小程序端已更新API调用逻辑 