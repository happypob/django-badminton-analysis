# ESP32-S3 传感器数据上传接口文档

## 📋 概述

本文档专门为ESP32-S3设备与后端系统的数据交互而设计。系统提供了专门优化的接口来处理来自ESP32-S3的传感器数据，支持实时数据流和批量数据上传。

## 🚀 接口列表

### 基础URL
```
http://your-domain/wxapp/esp32/
```

---

## 1. 单条数据上传接口

### 接口地址
```
POST /wxapp/esp32/upload/
```

### 功能描述
接收ESP32-S3上传的单条传感器数据

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| device_code | string | 是 | ESP32设备编码 |
| sensor_type | string | 是 | 传感器类型 |
| data | json | 是 | 传感器数据 |
| session_id | int | 否 | 会话ID |
| timestamp | string | 否 | ESP32时间戳 |

### 传感器类型
- `waist`: 腰部传感器
- `shoulder`: 肩部传感器  
- `wrist`: 腕部传感器
- `racket`: 球拍传感器

### 数据格式
```json
{
    "acc": [x, y, z],      // 加速度 (m/s²)
    "gyro": [x, y, z],     // 角速度 (rad/s)
    "angle": [x, y, z]     // 角度 (度)
}
```

### 请求示例
```bash
curl -X POST http://localhost:8000/wxapp/esp32/upload/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "device_code=esp32_001&sensor_type=waist&data={\"acc\":[1.2,0.8,9.8],\"gyro\":[0.1,0.2,0.3],\"angle\":[45.0,30.0,60.0]}&timestamp=1640995200"
```

### 响应示例
```json
{
    "msg": "ESP32 data upload success",
    "data_id": 123,
    "device_code": "esp32_001",
    "sensor_type": "waist",
    "timestamp": "2024-01-01T12:00:00Z",
    "session_id": 456,
    "session_status": "collecting"
}
```

---

## 2. 批量数据上传接口

### 接口地址
```
POST /wxapp/esp32/batch_upload/
```

### 功能描述
接收ESP32-S3上传的批量传感器数据，提高传输效率

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| device_code | string | 是 | ESP32设备编码 |
| sensor_type | string | 是 | 传感器类型 |
| batch_data | json array | 是 | 批量传感器数据 |
| session_id | int | 否 | 会话ID |

### 请求示例
```bash
curl -X POST http://localhost:8000/wxapp/esp32/batch_upload/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "device_code=esp32_001&sensor_type=waist&batch_data=[{\"acc\":[1.2,0.8,9.8],\"gyro\":[0.1,0.2,0.3],\"angle\":[45.0,30.0,60.0]},{\"acc\":[1.3,0.9,9.8],\"gyro\":[0.11,0.21,0.31],\"angle\":[46.0,31.0,61.0]}]"
```

### 响应示例
```json
{
    "msg": "Batch upload completed",
    "total_items": 2,
    "successful_items": 2,
    "failed_items": 0,
    "results": [
        {
            "index": 0,
            "data_id": 123,
            "timestamp": "2024-01-01T12:00:00Z"
        },
        {
            "index": 1,
            "data_id": 124,
            "timestamp": "2024-01-01T12:00:01Z"
        }
    ]
}
```

---

## 3. 设备状态检查接口

### 接口地址
```
POST /wxapp/esp32/status/
```

### 功能描述
检查ESP32设备的状态信息，包括绑定状态、数据统计等

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| device_code | string | 是 | ESP32设备编码 |

### 请求示例
```bash
curl -X POST http://localhost:8000/wxapp/esp32/status/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "device_code=esp32_001"
```

### 响应示例
```json
{
    "device_code": "esp32_001",
    "is_bound": true,
    "last_data_time": "2024-01-01T12:00:00Z",
    "total_data_count": 150,
    "active_sessions": [
        {
            "session_id": 456,
            "status": "collecting",
            "start_time": "2024-01-01T11:55:00Z"
        }
    ]
}
```

---

## 4. API信息接口

### 接口地址
```
GET /wxapp/esp32/upload/
```

### 功能描述
获取ESP32上传接口的详细信息和使用说明

### 请求示例
```bash
curl -X GET http://localhost:8000/wxapp/esp32/upload/
```

### 响应示例
```json
{
    "msg": "ESP32 Sensor Data Upload API",
    "method": "POST",
    "required_params": {
        "device_code": "string - ESP32设备编码",
        "sensor_type": "string - 传感器类型 (waist/shoulder/wrist/racket)",
        "data": "json - 传感器数据",
        "session_id": "int - 会话ID (可选)",
        "timestamp": "string - ESP32时间戳 (可选)"
    },
    "data_format": {
        "acc": "[x, y, z] - 加速度数据",
        "gyro": "[x, y, z] - 角速度数据",
        "angle": "[x, y, z] - 角度数据"
    },
    "example": {
        "device_code": "esp32_001",
        "sensor_type": "waist",
        "data": "{\"acc\":[1.2,0.8,9.8],\"gyro\":[0.1,0.2,0.3],\"angle\":[45.0,30.0,60.0]}",
        "session_id": "123",
        "timestamp": "1640995200"
    }
}
```

---

## 🔧 ESP32端实现建议

### 1. 数据采集频率
- **实时模式**: 100Hz (每10ms发送一次)
- **批量模式**: 50Hz (每20ms发送一次，每次发送多条数据)

### 2. 网络连接
```cpp
// ESP32 WiFi连接示例
const char* ssid = "your_wifi_ssid";
const char* password = "your_wifi_password";
const char* server_url = "http://your-domain/wxapp/esp32/upload/";
```

### 3. 数据格式转换
```cpp
// ESP32数据格式示例
struct SensorData {
    float acc[3];    // 加速度 x, y, z
    float gyro[3];   // 角速度 x, y, z  
    float angle[3];  // 角度 x, y, z
};

// 转换为JSON格式
String createJsonData(SensorData data) {
    String json = "{";
    json += "\"acc\":[" + String(data.acc[0]) + "," + String(data.acc[1]) + "," + String(data.acc[2]) + "],";
    json += "\"gyro\":[" + String(data.gyro[0]) + "," + String(data.gyro[1]) + "," + String(data.gyro[2]) + "],";
    json += "\"angle\":[" + String(data.angle[0]) + "," + String(data.angle[1]) + "," + String(data.angle[2]) + "]";
    json += "}";
    return json;
}
```

### 4. HTTP请求示例
```cpp
void uploadSensorData(String deviceCode, String sensorType, String data) {
    HTTPClient http;
    http.begin(server_url);
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    
    String postData = "device_code=" + deviceCode;
    postData += "&sensor_type=" + sensorType;
    postData += "&data=" + data;
    postData += "&timestamp=" + String(millis());
    
    int httpResponseCode = http.POST(postData);
    
    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.println("HTTP Response: " + response);
    } else {
        Serial.println("HTTP Error: " + String(httpResponseCode));
    }
    
    http.end();
}
```

---

## 📊 错误处理

### 常见错误码

| 状态码 | 错误信息 | 解决方案 |
|--------|----------|----------|
| 400 | Missing required parameters | 检查必需参数是否完整 |
| 400 | Invalid sensor_type | 确保传感器类型正确 |
| 400 | Invalid JSON data format | 检查数据JSON格式 |
| 400 | Missing required field | 确保数据包含所有必需字段 |
| 404 | Session not found | 检查会话ID是否正确 |
| 500 | Processing error | 检查服务器日志 |

### 错误响应格式
```json
{
    "error": "错误描述信息",
    "required": ["参数1", "参数2"]  // 可选，显示缺少的参数
}
```

---

## 🧪 测试工具

### 使用测试脚本
```bash
python test_esp32_api.py
```

### 测试内容
- ✅ 单条数据上传测试
- ✅ 批量数据上传测试  
- ✅ 设备状态检查测试
- ✅ API信息获取测试
- ✅ 会话管理测试

---

## 📈 性能优化建议

### 1. 数据压缩
- 使用批量上传减少HTTP请求次数
- 考虑使用gzip压缩数据

### 2. 连接优化
- 使用HTTP Keep-Alive
- 实现连接池管理
- 添加重试机制

### 3. 数据缓存
- 在ESP32端缓存数据
- 网络断开时本地存储
- 网络恢复后批量上传

---

## 🔒 安全考虑

### 1. 数据验证
- 所有输入数据都进行格式验证
- 防止恶意数据注入

### 2. 设备认证
- 使用设备编码进行身份验证
- 考虑添加API密钥机制

### 3. 数据传输
- 使用HTTPS加密传输
- 考虑添加数据签名验证

---

## 📞 技术支持

如有技术问题，请联系开发团队或查看系统日志获取详细信息。

---

*文档版本: v1.0*  
*最后更新: 2024年* 