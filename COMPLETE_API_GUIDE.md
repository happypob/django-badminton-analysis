# 完整API使用指南

## 概述

本系统采用SD卡存储 + 一次性上传的方式，每次采集都创建新的会话，避免数据覆盖，确保每次分析都是基于独立的会话数据。

## 完整工作流程

```
小程序开始采集 → 创建新会话 → 通知ESP32 → ESP32开始SD卡存储
小程序结束采集 → ESP32停止接收 → 上传SD卡数据 → 标记完成 → 自动分析
```

## API接口列表

### 1. 会话管理接口

#### 1.1 创建采集会话
- **URL**: `POST /wxapp/start_session/`
- **参数**:
  - `openid`: 用户openid
  - `device_group_code`: 设备组代码
- **响应**:
```json
{
    "msg": "session started",
    "session_id": 1015,
    "status": "calibrating"
}
```

#### 1.2 开始数据采集
- **URL**: `POST /wxapp/start_data_collection/`
- **参数**:
  - `session_id`: 会话ID
- **响应**:
```json
{
    "msg": "Data collection started",
    "session_id": 1015,
    "status": "collecting"
}
```

#### 1.3 结束采集会话
- **URL**: `POST /wxapp/end_session/`
- **参数**:
  - `session_id`: 会话ID
- **响应**:
```json
{
    "msg": "session ended",
    "session_id": 1015,
    "status": "stopped"
}
```

### 2. ESP32设备管理接口

#### 2.1 注册设备IP
- **URL**: `POST /wxapp/register_device_ip/`
- **参数**:
  - `device_code`: 设备码 (如: "2025001")
  - `ip_address`: ESP32的IP地址
- **响应**:
```json
{
    "msg": "Device 2025001 IP registered successfully",
    "device_code": "2025001",
    "ip_address": "192.168.1.100"
}
```

#### 2.2 通知设备开始采集
- **URL**: `POST /wxapp/notify_device_start/`
- **参数**:
  - `session_id`: 会话ID
  - `device_code`: 设备码
- **响应**:
```json
{
    "msg": "Device 2025001 notified to start collection",
    "session_id": 1015,
    "device_code": "2025001",
    "esp32_ip": "192.168.1.100",
    "esp32_response": "Collection started"
}
```

#### 2.3 获取设备状态
- **URL**: `GET /wxapp/get_device_status/`
- **参数**:
  - `device_code`: 设备码
- **响应**:
```json
{
    "msg": "Device status",
    "device_code": "2025001",
    "status": "collecting",
    "ip_address": "192.168.1.100"
}
```

### 3. ESP32数据上传接口

#### 3.1 批量上传传感器数据
- **URL**: `POST /wxapp/esp32/batch_upload/`
- **参数**:
  - `device_code`: 设备码
  - `sensor_type`: 传感器类型 ("waist", "shoulder", "wrist", "racket")
  - `session_id`: 会话ID
  - `batch_data`: JSON数组格式的传感器数据
- **响应**:
```json
{
    "msg": "Batch upload completed",
    "total_items": 10,
    "successful_items": 10,
    "failed_items": 0,
    "results": [...]
}
```

#### 3.2 标记上传完成
- **URL**: `POST /wxapp/esp32/mark_upload_complete/`
- **参数**:
  - `session_id`: 会话ID
  - `device_code`: 设备码
  - `upload_stats`: 上传统计信息JSON (可选)
- **响应**:
```json
{
    "msg": "ESP32 data upload completed and analysis triggered",
    "session_id": 1015,
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

### 4. 分析结果接口

#### 4.1 获取分析结果
- **URL**: `GET /wxapp/get_analysis/`
- **参数**:
  - `session_id`: 会话ID
- **响应**:
```json
{
    "msg": "Analysis result",
    "session_id": 1015,
    "analysis_id": 456,
    "status": "completed",
    "results": {...}
}
```

## 小程序端调用示例

```javascript
// 1. 创建新会话
wx.request({
  url: 'http://47.122.129.159:8000/wxapp/start_session/',
  method: 'POST',
  data: {
    openid: '用户openid',
    device_group_code: 'test_group_001'
  },
  success: function(res) {
    const sessionId = res.data.session_id;
    console.log('新会话ID:', sessionId);
    
    // 2. 开始数据采集
    wx.request({
      url: 'http://47.122.129.159:8000/wxapp/start_data_collection/',
      method: 'POST',
      data: {
        session_id: sessionId
      },
      success: function(res) {
        
        // 3. 通知ESP32开始采集
        wx.request({
          url: 'http://47.122.129.159:8000/wxapp/notify_device_start/',
          method: 'POST',
          data: {
            session_id: sessionId,
            device_code: '2025001'
          },
          success: function(res) {
            console.log('ESP32通知成功:', res.data);
          }
        });
      }
    });
  }
});

// 4. 结束采集
wx.request({
  url: 'http://47.122.129.159:8000/wxapp/end_session/',
  method: 'POST',
  data: {
    session_id: sessionId
  },
  success: function(res) {
    console.log('采集结束:', res.data);
  }
});
```

## ESP32端实现要点

### 1. 启动时注册IP
```cpp
// ESP32启动时调用
POST /wxapp/register_device_ip/
{
    "device_code": "2025001",
    "ip_address": "192.168.1.100"
}
```

### 2. 监听开始采集消息
```cpp
// ESP32 WebServer端点
server.on("/start_collection", HTTP_POST, [](AsyncWebServerRequest *request) {
    String sessionId = request->getParam("session_id", true)->value();
    String deviceCode = request->getParam("device_code", true)->value();
    
    // 保存会话ID，开始SD卡存储
    currentSessionId = sessionId;
    startDataCollection();
    
    request->send(200, "application/json", "{\"msg\": \"Collection started\"}");
});
```

### 3. 上传数据时使用会话ID
```cpp
// 上传数据时
POST /wxapp/esp32/batch_upload/
{
    "session_id": currentSessionId,
    "device_code": "2025001",
    "sensor_type": "waist",
    "batch_data": [...]
}
```

### 4. 标记上传完成
```cpp
// 上传完成后调用
POST /wxapp/esp32/mark_upload_complete/
{
    "session_id": currentSessionId,
    "device_code": "2025001",
    "upload_stats": "{\"total_files\": 3, \"total_bytes\": 1024000}"
}
```

## 测试命令

```bash
# 1. 注册ESP32 IP
curl -X POST "http://47.122.129.159:8000/wxapp/register_device_ip/" \
  -d "device_code=2025001&ip_address=192.168.1.100"

# 2. 创建新会话
curl -X POST "http://47.122.129.159:8000/wxapp/start_session/" \
  -d "openid=test_user&device_group_code=test_group"

# 3. 开始数据采集
curl -X POST "http://47.122.129.159:8000/wxapp/start_data_collection/" \
  -d "session_id=1015"

# 4. 通知ESP32
curl -X POST "http://47.122.129.159:8000/wxapp/notify_device_start/" \
  -d "session_id=1015&device_code=2025001"

# 5. 上传传感器数据
curl -X POST "http://47.122.129.159:8000/wxapp/esp32/batch_upload/" \
  -d "session_id=1015&device_code=2025001&sensor_type=waist&batch_data=[{\"acc\":[1.2,2.3,9.8],\"gyro\":[0.1,0.2,0.3],\"angle\":[45.0,30.0,60.0]}]"

# 6. 标记上传完成
curl -X POST "http://47.122.129.159:8000/wxapp/esp32/mark_upload_complete/" \
  -d "session_id=1015&device_code=2025001&upload_stats={\"total_files\":3}"
```

## 关键优势

1. **避免数据覆盖**: 每次采集创建新会话
2. **独立分析**: 每次分析基于独立的会话数据
3. **自动触发**: ESP32标记完成后自动开始分析
4. **完整流程**: 从创建会话到数据分析的完整自动化流程

## 注意事项

1. **设备码统一**: 使用 `2025001`
2. **会话ID传递**: ESP32必须保存并使用正确的会话ID
3. **错误处理**: 需要处理网络错误和重试机制
4. **状态同步**: 确保会话状态正确转换 