# 🏸 羽毛球数据分析系统 API 文档

## 📋 概述

本系统提供羽毛球运动数据采集、分析和UDP广播控制功能。支持ESP32设备通过UDP广播接收控制指令，实现远程数据采集管理。

### 🌐 服务器信息
- **服务器地址**: `http://47.122.129.159:8000`
- **UDP广播端口**: `8888`
- **UDP广播地址**: `255.255.255.255`

---

## 🔐 用户认证

### 微信登录
```http
POST /wxapp/wx_login/
```

**请求参数:**
- `code` (string, required): 微信小程序登录code

**响应示例:**
```json
{
  "msg": "ok",
  "openid": "user_openid_123",
  "user_id": 1
}
```

---

## 📱 设备管理

### 绑定设备
```http
POST /wxapp/bind_device/
```

**请求参数:**
- `openid` (string, required): 用户openid
- `device_code` (string, required): 设备编码

**响应示例:**
```json
{
  "msg": "设备绑定成功",
  "device_code": "2025001"
}
```

---

## 🚀 数据采集会话

### 开始数据采集（自动创建会话）
```http
POST /wxapp/start_data_collection/
```

**请求参数:**
- `openid` (string, required): 用户openid
- `device_group_code` (string, required): 设备组编码
- `device_code` (string, optional): 设备码，默认"2025001"

**功能说明:**
- 自动创建新的采集会话
- 会话状态为 `calibrating`
- 发送UDP广播通知ESP32开始校准
- 广播消息包含会话ID和设备码

**响应示例:**
```json
{
  "msg": "Data collection started and ESP32 notified",
  "session_id": 1015,
  "status": "calibrating",
  "device_code": "2025001",
  "broadcast_message": "{\"command\":\"START_COLLECTION\",\"session_id\":\"1015\",\"device_code\":\"2025001\",\"timestamp\":\"2025-08-05T06:25:24.283680\"}",
  "broadcast_port": 8888,
  "timestamp": "2025-08-05T06:25:24.283680"
}
```

### 结束数据采集
```http
POST /wxapp/start_data_collection/
```

**请求参数:**
- `session_id` (int, required): 会话ID
- `device_code` (string, optional): 设备码，默认"2025001"

**功能说明:**
- 将会话状态从`calibrating`变为`collecting`
- 发送UDP广播通知ESP32开始采集
- 广播消息包含会话ID和设备码

**响应示例:**
```json
{
  "msg": "Data collection started and ESP32 notified",
  "session_id": 1015,
  "status": "collecting",
  "device_code": "2025001",
  "broadcast_message": "{\"command\":\"START_COLLECTION\",\"session_id\":\"1015\",\"device_code\":\"2025001\",\"timestamp\":\"2025-08-05T06:25:24.283680\"}",
  "broadcast_port": 8888,
  "timestamp": "2025-08-05T06:25:24.283680"
}
```

### 结束数据采集
```http
POST /wxapp/end_session/
```

**请求参数:**
- `session_id` (int, required): 会话ID
- `device_code` (string, optional): 设备码，默认"2025001"

**功能说明:**
- 发送UDP广播通知ESP32停止采集
- 将会话状态变为`analyzing`
- 自动开始数据分析

**响应示例:**
```json
{
  "msg": "Session ended, ESP32 notified, and analysis started",
  "session_id": 1015,
  "analysis_id": 11,
  "status": "analyzing",
  "device_code": "2025001",
  "broadcast_message": "{\"command\":\"STOP_COLLECTION\",\"device_code\":\"2025001\",\"session_id\":\"1015\",\"timestamp\":\"2025-08-05T06:25:24.308693\"}",
  "broadcast_port": 8888
}
```

---

## 📡 UDP广播控制

### 测试UDP广播
```http
POST /wxapp/test_udp_broadcast/
```

**请求参数:**
- `message` (string, optional): 自定义测试消息，默认"TEST_BROADCAST"
- `device_code` (string, optional): 设备码，默认"2025001"

**响应示例:**
```json
{
  "msg": "UDP广播测试成功",
  "device_code": "2025001",
  "broadcast_message": "{\"command\":\"TEST\",\"message\":\"Hello ESP32!\",\"device_code\":\"2025001\",\"timestamp\":\"2025-08-05T06:25:24.223820\"}",
  "broadcast_port": 8888,
  "result": "广播发送成功"
}
```

### 通知ESP32开始采集
```http
POST /wxapp/notify_esp32_start/
```

**请求参数:**
- `session_id` (int, required): 会话ID
- `device_code` (string, optional): 设备码，默认"2025001"

**响应示例:**
```json
{
  "msg": "UDP广播发送成功，ESP32应该收到开始采集指令",
  "session_id": 1015,
  "device_code": "2025001",
  "broadcast_message": "{\"command\":\"START_COLLECTION\",\"session_id\":\"1015\",\"device_code\":\"2025001\",\"timestamp\":\"2025-08-05T06:25:24.283680\"}",
  "broadcast_port": 8888
}
```

### 通知ESP32停止采集
```http
POST /wxapp/notify_esp32_stop/
```

**请求参数:**
- `device_code` (string, optional): 设备码，默认"2025001"

**响应示例:**
```json
{
  "msg": "UDP广播发送成功，ESP32应该收到停止采集指令",
  "device_code": "2025001",
  "broadcast_message": "{\"command\":\"STOP_COLLECTION\",\"device_code\":\"2025001\",\"timestamp\":\"2025-08-05T06:25:24.308693\"}",
  "broadcast_port": 8888
}
```

---

## 📊 数据上传

### ESP32传感器数据上传
```http
POST /wxapp/esp32/upload/
```

**请求参数:**
- `session_id` (int, required): 会话ID
- `device_code` (string, required): 设备编码
- `sensor_type` (string, required): 传感器类型 (waist/shoulder/wrist/racket)
- `data` (string, required): JSON格式的传感器数据

**响应示例:**
```json
{
  "msg": "数据上传成功",
  "session_id": 1015,
  "device_code": "2025001",
  "sensor_type": "waist",
  "data_count": 100
}
```

### ESP32批量数据上传
```http
POST /wxapp/esp32/batch_upload/
```

**请求参数:**
- `session_id` (int, required): 会话ID
- `device_code` (string, required): 设备编码
- `data_batch` (string, required): JSON数组格式的批量数据

**响应示例:**
```json
{
  "msg": "批量数据上传成功",
  "session_id": 1015,
  "device_code": "2025001",
  "total_count": 500,
  "success_count": 500,
  "failed_count": 0
}
```

---

## 📈 数据分析

### 获取分析结果
```http
GET /wxapp/get_analysis_result/
```

**请求参数:**
- `session_id` (int, required): 会话ID

**响应示例:**
```json
{
  "msg": "分析结果获取成功",
  "session_id": 1015,
  "analysis_id": 11,
  "phase_delay": {
    "backswing_delay": 0.15,
    "forward_delay": 0.08
  },
  "energy_ratio": 0.85,
  "rom_data": {
    "shoulder_rom": 120,
    "wrist_rom": 90
  },
  "score": 85,
  "recommendations": [
    "建议增加肩部活动度训练",
    "注意击球时机，减少延迟"
  ]
}
```

### 生成详细报告
```http
GET /wxapp/generate_analysis_report/
```

**请求参数:**
- `session_id` (int, required): 会话ID

**响应示例:**
```json
{
  "msg": "详细报告生成成功",
  "session_id": 1015,
  "report_url": "/media/reports/session_1015_report.pdf",
  "charts": [
    "/media/charts/session_1015_phase_delay.png",
    "/media/charts/session_1015_energy_analysis.png"
  ]
}
```

---

## 🔧 设备状态

### 注册设备IP
```http
POST /wxapp/register_device_ip/
```

**请求参数:**
- `device_code` (string, required): 设备编码
- `ip_address` (string, required): 设备IP地址

**响应示例:**
```json
{
  "msg": "设备IP注册成功",
  "device_code": "2025001",
  "ip_address": "192.168.1.100"
}
```

### 获取设备状态
```http
GET /wxapp/get_device_status/
```

**请求参数:**
- `device_code` (string, required): 设备编码

**响应示例:**
```json
{
  "msg": "设备状态获取成功",
  "device_code": "2025001",
  "status": "online",
  "ip_address": "192.168.1.100",
  "last_seen": "2025-08-05T06:25:24.308693",
  "session_id": 1015
}
```

---

## 📋 会话状态说明

### 会话状态流程
1. **calibrating** (校准中) - 初始状态，ESP32进行传感器校准
2. **collecting** (采集中) - 开始正式数据采集，ESP32上传传感器数据
3. **analyzing** (分析中) - 结束采集，开始数据分析
4. **completed** (已完成) - 分析完成，可查看结果
5. **stopped** (已停止) - 手动停止采集

---

## 📡 UDP广播消息格式

### 开始采集消息
```json
{
  "command": "START_COLLECTION",
  "session_id": "1015",
  "device_code": "2025001",
  "timestamp": "2025-08-05T06:25:24.283680"
}
```

### 停止采集消息
```json
{
  "command": "STOP_COLLECTION",
  "device_code": "2025001",
  "session_id": "1015",
  "timestamp": "2025-08-05T06:25:24.308693"
}
```

### 测试消息
```json
{
  "command": "TEST",
  "message": "Hello ESP32!",
  "device_code": "2025001",
  "timestamp": "2025-08-05T06:25:24.223820"
}
```

---

## 🧪 测试命令

### 本地测试
```bash
# 测试UDP广播
curl -X POST http://localhost:8000/wxapp/test_udp_broadcast/ \
  -d "message=Hello ESP32!" \
  -d "device_code=2025001"

# 创建会话
curl -X POST http://localhost:8000/wxapp/start_session/ \
  -d "openid=test_user_123456" \
  -d "device_group_code=2025001"

# 开始采集
curl -X POST http://localhost:8000/wxapp/start_data_collection/ \
  -d "session_id=1015" \
  -d "device_code=2025001"

# 结束采集
curl -X POST http://localhost:8000/wxapp/end_session/ \
  -d "session_id=1015" \
  -d "device_code=2025001"
```

### 服务器测试
```bash
# 测试UDP广播
curl -X POST http://47.122.129.159:8000/wxapp/test_udp_broadcast/ \
  -d "message=Hello ESP32 from server!" \
  -d "device_code=2025001"

# 创建会话
curl -X POST http://47.122.129.159:8000/wxapp/start_session/ \
  -d "openid=test_user_123456" \
  -d "device_group_code=2025001"

# 开始采集
curl -X POST http://47.122.129.159:8000/wxapp/start_data_collection/ \
  -d "session_id=1015" \
  -d "device_code=2025001"

# 结束采集
curl -X POST http://47.122.129.159:8000/wxapp/end_session/ \
  -d "session_id=1015" \
  -d "device_code=2025001"
```

---

## 📝 错误代码

| 错误代码 | 说明 |
|---------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 🔗 相关文档

- [ESP32 UDP广播监听指南](./ESP32_UDP_BROADCAST_GUIDE.md)
- [部署指南](./DEPLOYMENT_GUIDE.md)
- [UDP广播API指南](./UDP_BROADCAST_API_GUIDE.md)

---

*最后更新: 2025-08-05* 