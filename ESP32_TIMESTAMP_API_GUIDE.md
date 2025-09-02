# 🕐 ESP32精确时间戳功能 - API指南

## 📋 功能概述

ESP32批量上传接口现在支持精确的设备端时间戳，允许ESP32发送每条数据的精确采集时间，提供更准确的时间同步和数据分析能力。

## 🚀 核心特性

- ✅ **双时间戳系统**: 同时记录服务器时间戳和ESP32设备时间戳
- ✅ **多格式支持**: 支持Unix时间戳（毫秒）和ISO格式字符串
- ✅ **容错处理**: 无效时间戳会被忽略，数据仍正常保存
- ✅ **向后兼容**: 不影响现有不包含时间戳的数据上传

## 📡 API接口详情

### 批量上传接口

**接口地址**: `/wxapp/esp32/batch_upload/`  
**请求方法**: `POST`  
**内容类型**: `application/x-www-form-urlencoded`

### 📋 请求参数

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| `batch_data` | JSON字符串 | ✅ | 批量传感器数据数组 |
| `device_code` | 字符串 | ✅ | ESP32设备编码 |
| `sensor_type` | 字符串 | ✅ | 传感器类型 (waist/shoulder/wrist/racket) |
| `session_id` | 字符串 | ❌ | 数据采集会话ID (可选) |

### 📊 batch_data 数据格式

每个数据项包含以下字段：

```json
{
  "acc": [x, y, z],      // 加速度数据 (必需)
  "gyro": [x, y, z],     // 角速度数据 (必需)
  "angle": [x, y, z],    // 角度数据 (必需)
  "timestamp": <时间戳>   // ESP32时间戳 (可选)
}
```

### ⏰ 时间戳格式支持

#### 1. Unix时间戳（毫秒）
```json
{
  "acc": [1.2, -0.5, 9.8],
  "gyro": [0.1, 0.2, 0.3],
  "angle": [10.5, 20.3, 30.1],
  "timestamp": 1693574400000
}
```

#### 2. ISO格式字符串
```json
{
  "acc": [1.2, -0.5, 9.8],
  "gyro": [0.1, 0.2, 0.3],
  "angle": [10.5, 20.3, 30.1],
  "timestamp": "2025-09-01T15:30:00.000Z"
}
```

#### 3. 不包含时间戳
```json
{
  "acc": [1.2, -0.5, 9.8],
  "gyro": [0.1, 0.2, 0.3],
  "angle": [10.5, 20.3, 30.1]
}
```

## 📤 请求示例

### cURL示例
```bash
curl -X POST http://your-server:8000/wxapp/esp32/batch_upload/ \\
  -d "device_code=esp32s3_multi_001" \\
  -d "sensor_type=waist" \\
  -d "session_id=123" \\
  -d 'batch_data=[
    {
      "acc": [1.2, -0.5, 9.8],
      "gyro": [0.1, 0.2, 0.3],
      "angle": [10.5, 20.3, 30.1],
      "timestamp": 1693574400000
    },
    {
      "acc": [1.3, -0.6, 9.7],
      "gyro": [0.2, 0.3, 0.4],
      "angle": [11.5, 21.3, 31.1],
      "timestamp": 1693574400100
    }
  ]'
```

### ESP32 Arduino代码示例
```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

void uploadSensorData() {
    HTTPClient http;
    http.begin("http://your-server:8000/wxapp/esp32/batch_upload/");
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    
    // 获取当前时间戳（毫秒）
    unsigned long timestamp = millis() + time_offset;
    
    // 构建JSON数据
    DynamicJsonDocument doc(2048);
    JsonArray batch = doc.createNestedArray();
    
    JsonObject data1 = batch.createNestedObject();
    JsonArray acc1 = data1.createNestedArray("acc");
    acc1.add(1.2); acc1.add(-0.5); acc1.add(9.8);
    JsonArray gyro1 = data1.createNestedArray("gyro");
    gyro1.add(0.1); gyro1.add(0.2); gyro1.add(0.3);
    JsonArray angle1 = data1.createNestedArray("angle");
    angle1.add(10.5); angle1.add(20.3); angle1.add(30.1);
    data1["timestamp"] = timestamp;
    
    String batchData;
    serializeJson(doc, batchData);
    
    String postData = "device_code=esp32s3_multi_001";
    postData += "&sensor_type=waist";
    postData += "&session_id=123";
    postData += "&batch_data=" + batchData;
    
    int httpResponseCode = http.POST(postData);
    String response = http.getString();
    
    http.end();
}
```

## 📥 响应格式

### 成功响应 (200)
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
      "server_timestamp": "2025-09-02T03:11:49.993870+00:00",
      "esp32_timestamp": "2025-09-02T03:11:49.981000+00:00"
    },
    {
      "index": 1,
      "data_id": 124,
      "server_timestamp": "2025-09-02T03:11:50.009607+00:00",
      "esp32_timestamp": "2025-09-02T03:11:50.081000+00:00"
    }
  ]
}
```

### 错误响应 (400)
```json
{
  "error": "Missing required parameters",
  "required": ["batch_data", "device_code", "sensor_type"]
}
```

## 🔧 数据库存储

### SensorData模型字段
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `timestamp` | DateTimeField | 服务器接收时间戳（自动生成） |
| `esp32_timestamp` | DateTimeField | ESP32设备采集时间戳（可选） |
| `device_code` | CharField | 设备编码 |
| `sensor_type` | CharField | 传感器类型 |
| `data` | TextField | JSON格式的传感器数据 |

### 查询示例
```python
from wxapp.models import SensorData

# 查询有ESP32时间戳的数据
data_with_esp32_time = SensorData.objects.filter(
    esp32_timestamp__isnull=False
)

# 按ESP32时间戳排序
data_by_esp32_time = SensorData.objects.filter(
    esp32_timestamp__isnull=False
).order_by('esp32_timestamp')

# 计算时间差
for data in data_with_esp32_time:
    time_diff = data.timestamp - data.esp32_timestamp
    print(f"传输延迟: {time_diff.total_seconds():.3f}秒")
```

## 🎯 使用场景

### 1. 高精度运动分析
- 使用ESP32时间戳进行精确的动作时序分析
- 多传感器数据的精确时间同步
- 运动轨迹的时间精度优化

### 2. 网络延迟分析
- 对比服务器时间戳和ESP32时间戳
- 分析数据传输延迟
- 网络质量监控

### 3. 设备同步
- 多个ESP32设备的时间同步
- 分布式传感器网络的协调
- 实时数据流的时间校准

## ⚠️ 注意事项

1. **时间同步**: ESP32需要通过NTP服务器同步时间
2. **时区处理**: 建议使用UTC时间戳避免时区问题
3. **精度限制**: 毫秒级精度，适合大多数运动分析场景
4. **容错设计**: 无效时间戳不会影响数据保存
5. **存储开销**: 每条记录额外存储8字节时间戳数据

## 🧪 测试工具

项目包含完整的测试脚本：
- `test_esp32_timestamp.py` - 功能测试脚本
- `check_esp32_timestamp_data.py` - 数据检查脚本

运行测试：
```bash
python test_esp32_timestamp.py
python check_esp32_timestamp_data.py
```

## 📈 性能优化建议

1. **批量上传**: 建议每次上传10-50条数据
2. **时间戳缓存**: ESP32端缓存时间戳减少NTP查询
3. **数据压缩**: 大量数据时考虑JSON压缩
4. **异步处理**: 服务端异步处理大批量数据

---

## 🔗 相关文档

- [ESP32_API_DOCUMENTATION.md](ESP32_API_DOCUMENTATION.md) - ESP32 API完整文档
- [API_DOCUMENTATION_V2.md](API_DOCUMENTATION_V2.md) - 系统API文档
- [云服务器管理指令文档.md](云服务器管理指令文档.md) - 服务器运维指南 