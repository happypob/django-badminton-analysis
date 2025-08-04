# UDP广播API使用指南

## 📡 概述

后端现在使用UDP广播来通知ESP32开始/停止数据采集，而不是直接发送HTTP请求。这样可以绕过网络限制，让ESP32主动监听广播消息。

## 🔧 配置

### UDP广播配置
- **广播端口**: 8888
- **广播地址**: 255.255.255.255
- **消息格式**: JSON字符串

## 📋 API接口

### 1. 测试UDP广播
**接口**: `POST /wxapp/test_udp_broadcast/`

**功能**: 测试UDP广播功能是否正常

**参数**:
- `message` (可选): 自定义测试消息
- `device_code` (可选): 设备码，默认2025001

**示例**:
```bash
curl -X POST http://47.122.129.159:8000/wxapp/test_udp_broadcast/ \
  -d "message=Hello ESP32!" \
  -d "device_code=2025001"
```

**响应**:
```json
{
  "msg": "UDP广播测试成功",
  "device_code": "2025001",
  "broadcast_message": "{\"command\":\"TEST\",\"message\":\"Hello ESP32!\",\"device_code\":\"2025001\",\"timestamp\":\"2024-01-01T12:00:00\"}",
  "broadcast_port": 8888,
  "result": "广播发送成功"
}
```

### 2. 开始采集广播
**接口**: `POST /wxapp/notify_esp32_start/`

**功能**: 通过UDP广播通知ESP32开始数据采集

**参数**:
- `session_id`: 会话ID
- `device_code` (可选): 设备码，默认2025001

**示例**:
```bash
curl -X POST http://47.122.129.159:8000/wxapp/notify_esp32_start/ \
  -d "session_id=123" \
  -d "device_code=2025001"
```

**响应**:
```json
{
  "msg": "UDP广播发送成功，ESP32应该收到开始采集指令",
  "session_id": "123",
  "device_code": "2025001",
  "broadcast_message": "{\"command\":\"START_COLLECTION\",\"session_id\":\"123\",\"device_code\":\"2025001\",\"timestamp\":\"2024-01-01T12:00:00\"}",
  "broadcast_port": 8888
}
```

### 3. 结束会话（包含停止采集广播）
**接口**: `POST /wxapp/end_session/`

**功能**: 结束数据采集会话，发送UDP广播通知ESP32停止采集，并开始数据分析

**参数**:
- `session_id`: 会话ID
- `device_code` (可选): 设备码，默认2025001

**示例**:
```bash
curl -X POST http://47.122.129.159:8000/wxapp/end_session/ \
  -d "session_id=123" \
  -d "device_code=2025001"
```

**响应**:
```json
{
  "msg": "Session ended, ESP32 notified, and analysis started",
  "session_id": "123",
  "analysis_id": "456",
  "status": "analyzing",
  "device_code": "2025001",
  "broadcast_message": "{\"command\":\"STOP_COLLECTION\",\"device_code\":\"2025001\",\"session_id\":\"123\",\"timestamp\":\"2024-01-01T12:00:00\"}",
  "broadcast_port": 8888
}
```

## 📡 广播消息格式

### 开始采集消息
```json
{
  "command": "START_COLLECTION",
  "session_id": "123",
  "device_code": "2025001",
  "timestamp": "2024-01-01T12:00:00"
}
```

### 停止采集消息
```json
{
  "command": "STOP_COLLECTION",
  "device_code": "2025001",
  "timestamp": "2024-01-01T12:00:00"
}
```

### 测试消息
```json
{
  "command": "TEST",
  "message": "Hello ESP32!",
  "device_code": "2025001",
  "timestamp": "2024-01-01T12:00:00"
}
```

## 🔧 ESP32监听配置

ESP32需要监听UDP端口8888来接收广播消息：

```cpp
// ESP32 UDP监听配置
#define UDP_LISTEN_PORT 8888
#define UDP_BUFFER_SIZE 512

WiFiUDP udp;
char udpBuffer[UDP_BUFFER_SIZE];

void setupUDPListener() {
    udp.begin(UDP_LISTEN_PORT);
    Serial.printf("📡 UDP监听器启动，端口: %d\n", UDP_LISTEN_PORT);
}

void checkUDPMessages() {
    int packetSize = udp.parsePacket();
    if (packetSize) {
        int len = udp.read(udpBuffer, UDP_BUFFER_SIZE);
        udpBuffer[len] = 0;
        
        // 解析JSON消息
        StaticJsonDocument<512> doc;
        DeserializationError error = deserializeJson(doc, udpBuffer);
        
        if (!error) {
            const char* command = doc["command"];
            const char* device_code = doc["device_code"];
            
            // 检查设备码是否匹配
            if (strcmp(device_code, "2025001") != 0) {
                Serial.printf("⚠️ 设备码不匹配: %s (期望: 2025001)\n", device_code);
                return;
            }
            
            Serial.printf("📨 收到UDP消息: %s (设备码: %s)\n", command, device_code);
            
            if (strcmp(command, "START_COLLECTION") == 0) {
                // 开始采集
                const char* session_id = doc["session_id"];
                startDataCollection(session_id);
            } else if (strcmp(command, "STOP_COLLECTION") == 0) {
                // 停止采集
                stopDataCollection();
            } else if (strcmp(command, "TEST") == 0) {
                // 测试消息
                const char* message = doc["message"];
                Serial.printf("🧪 测试消息: %s\n", message);
            }
        }
    }
}
```

## 🧪 测试方法

### 1. 使用测试脚本
```bash
python test_udp_broadcast.py
```

### 2. 使用curl命令
```bash
# 测试广播
curl -X POST http://47.122.129.159:8000/wxapp/test_udp_broadcast/ \
  -d "message=Test message" \
  -d "device_code=2025001"

# 开始采集
curl -X POST http://47.122.129.159:8000/wxapp/notify_esp32_start/ \
  -d "session_id=123" \
  -d "device_code=2025001"

# 结束会话（包含停止采集广播）
curl -X POST http://47.122.129.159:8000/wxapp/end_session/ \
  -d "session_id=123" \
  -d "device_code=2025001"
```

## ⚠️ 注意事项

1. **网络环境**: 确保ESP32和服务器在同一局域网内
2. **防火墙**: 确保UDP端口8888没有被防火墙阻止
3. **广播权限**: 某些网络环境可能限制广播消息
4. **消息大小**: JSON消息不应超过512字节

## 🔍 故障排除

### 1. ESP32收不到广播
- 检查ESP32是否正确监听端口8888
- 确认网络环境是否支持广播
- 检查防火墙设置

### 2. 广播发送失败
- 检查服务器网络配置
- 确认socket权限
- 查看服务器日志

### 3. 消息解析错误
- 检查JSON格式是否正确
- 确认ESP32的JSON解析库
- 验证消息编码格式

## 📝 更新日志

- **2024-01-01**: 初始版本，支持UDP广播通知
- 添加测试接口和完整的错误处理
- 支持开始/停止采集和测试消息 