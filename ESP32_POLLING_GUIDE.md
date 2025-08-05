# ESP32轮询指南

## 📋 概述

本文档详细说明ESP32设备如何通过轮询机制与服务器进行通信，获取开始/停止数据采集指令。

## 🚀 轮询接口信息

### 基本信息
- **接口地址**: `POST /wxapp/esp32/poll_commands/`
- **完整URL**: `http://您的服务器IP:8000/wxapp/esp32/poll_commands/`
- **轮询间隔**: 建议3-5秒
- **Content-Type**: `application/x-www-form-urlencoded`

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| device_code | string | 是 | 设备码 | "2025001" |
| current_session | string | 否 | 当前会话ID | "1015" |
| status | string | 否 | 当前状态 | "idle" 或 "collecting" |

## 📡 请求示例

### 基础轮询请求（空闲状态）
```bash
curl -X POST http://localhost:8000/wxapp/esp32/poll_commands/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "device_code=2025001&current_session=&status=idle"
```

### 正在采集时的轮询请求
```bash
curl -X POST http://localhost:8000/wxapp/esp32/poll_commands/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "device_code=2025001&current_session=1015&status=collecting"
```

## 📨 响应格式

### 1. 收到开始指令
```json
{
    "device_code": "2025001",
    "command": "START_COLLECTION",
    "session_id": "1015",
    "timestamp": "2025-08-05T08:48:31.123456",
    "message": "开始采集指令"
}
```

### 2. 收到停止指令
```json
{
    "device_code": "2025001",
    "command": "STOP_COLLECTION",
    "session_id": "1015",
    "timestamp": "2025-08-05T08:48:46.123456",
    "message": "停止采集指令"
}
```

### 3. 无新指令
```json
{
    "device_code": "2025001",
    "command": null,
    "current_session": "1015",
    "status": "collecting",
    "message": "无新指令"
}
```

### 4. 无会话
```json
{
    "device_code": "2025001",
    "command": null,
    "message": "No session found for device"
}
```

## 💻 完整的ESP32轮询代码

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// 配置信息
const char* ssid = "您的WiFi名称";
const char* password = "您的WiFi密码";
const char* serverUrl = "http://您的服务器IP:8000";
const String deviceCode = "2025001";

// 状态变量
bool isCollecting = false;
String currentSessionId = "";
unsigned long lastPolling = 0;
const unsigned long pollingInterval = 3000; // 3秒轮询一次

void setup() {
  Serial.begin(115200);
  Serial.println("🚀 ESP32轮询客户端启动");
  
  // 连接WiFi
  connectToWiFi();
  
  Serial.println("✅ 初始化完成，开始轮询...");
}

void loop() {
  // 检查WiFi连接
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi断开，重连中...");
    connectToWiFi();
    return;
  }
  
  // 定期轮询
  if (millis() - lastPolling > pollingInterval) {
    pollServerCommands();
    lastPolling = millis();
  }
  
  delay(100);
}

void pollServerCommands() {
  HTTPClient http;
  String url = String(serverUrl) + "/wxapp/esp32/poll_commands/";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");
  
  // 构建请求参数
  String postData = "device_code=" + deviceCode;
  
  // 添加当前会话ID（如果有）
  if (currentSessionId.length() > 0) {
    postData += "&current_session=" + currentSessionId;
  }
  
  // 添加当前状态
  postData += "&status=" + (isCollecting ? "collecting" : "idle");
  
  Serial.println("📡 发送轮询请求: " + postData);
  
  // 发送POST请求
  int httpResponseCode = http.POST(postData);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.print("📨 轮询响应 (");
    Serial.print(httpResponseCode);
    Serial.println("):");
    Serial.println(response);
    
    // 解析响应
    parseServerResponse(response);
  } else {
    Serial.print("❌ 轮询失败，错误码: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}

void parseServerResponse(String response) {
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, response);
  
  if (error) {
    Serial.println("❌ JSON解析失败:");
    Serial.println(error.c_str());
    return;
  }
  
  // 检查是否有指令
  if (doc.containsKey("command")) {
    const char* command = doc["command"];
    
    // 如果command为null，表示无新指令
    if (command == nullptr) {
      Serial.println("📭 无新指令");
      return;
    }
    
    const char* sessionId = doc["session_id"];
    const char* message = doc["message"];
    
    Serial.println("📨 收到服务器指令:");
    Serial.print("   指令: ");
    Serial.println(command);
    Serial.print("   会话ID: ");
    Serial.println(sessionId);
    Serial.print("   消息: ");
    Serial.println(message);
    
    // 处理指令
    if (strcmp(command, "START_COLLECTION") == 0) {
      startCollection(String(sessionId));
    } else if (strcmp(command, "STOP_COLLECTION") == 0) {
      stopCollection(String(sessionId));
    }
  } else {
    Serial.println("⚠️ 响应中没有command字段");
  }
}

void startCollection(String sessionId) {
  Serial.println("🟢 开始采集数据!");
  Serial.print("   会话ID: ");
  Serial.println(sessionId);
  
  isCollecting = true;
  currentSessionId = sessionId;
  
  // 发送状态确认
  sendStatusUpdate("START_COLLECTION_CONFIRMED", sessionId);
  
  // 开始您的数据采集逻辑
  Serial.println("📊 开始采集传感器数据...");
  // 在这里添加您的传感器数据采集代码
}

void stopCollection(String sessionId) {
  Serial.println("🔴 停止采集数据!");
  Serial.print("   会话ID: ");
  Serial.println(sessionId);
  
  isCollecting = false;
  currentSessionId = "";
  
  // 发送状态确认
  sendStatusUpdate("STOP_COLLECTION_CONFIRMED", sessionId);
  
  // 停止您的数据采集逻辑
  Serial.println("📊 停止采集传感器数据...");
  // 在这里添加停止采集的代码
}

void sendStatusUpdate(String status, String sessionId) {
  HTTPClient http;
  String url = String(serverUrl) + "/wxapp/esp32/status/";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");
  
  String postData = "status=" + status + 
                   "&session_id=" + sessionId + 
                   "&device_code=" + deviceCode;
  
  Serial.println("📤 发送状态更新: " + postData);
  
  int httpResponseCode = http.POST(postData);
  
  if (httpResponseCode > 0) {
    Serial.print("✅ 状态更新成功，响应码: ");
    Serial.println(httpResponseCode);
  } else {
    Serial.print("❌ 状态更新失败，错误码: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}

void connectToWiFi() {
  Serial.print("📶 连接到WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("✅ WiFi连接成功!");
    Serial.print("📡 IP地址: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("❌ WiFi连接失败!");
  }
}

// 打印当前状态
void printStatus() {
  Serial.println();
  Serial.println("📊 当前状态:");
  Serial.print("   WiFi状态: ");
  Serial.println(WiFi.status() == WL_CONNECTED ? "已连接" : "未连接");
  Serial.print("   采集状态: ");
  Serial.println(isCollecting ? "正在采集" : "未采集");
  Serial.print("   当前会话: ");
  Serial.println(currentSessionId.length() > 0 ? currentSessionId : "无");
  Serial.print("   设备码: ");
  Serial.println(deviceCode);
  Serial.println("================================");
}
```

## 🔄 轮询工作流程

### 1. 初始化阶段
- ESP32连接WiFi
- 开始定期轮询（每3秒一次）
- 初始状态：`isCollecting = false`, `currentSessionId = ""`

### 2. 等待指令阶段
- 轮询请求：`device_code=2025001&current_session=&status=idle`
- 服务器响应：`command: null`（无新指令）

### 3. 收到开始指令
- 服务器响应：`command: "START_COLLECTION"`
- ESP32开始采集，更新状态
- 后续轮询：`device_code=2025001&current_session=1015&status=collecting`

### 4. 收到停止指令
- 服务器响应：`command: "STOP_COLLECTION"`
- ESP32停止采集，清空会话ID
- 返回等待状态

## 🧪 测试方法

### 1. 使用curl测试轮询接口

```bash
# 测试轮询（空闲状态）
curl -X POST http://localhost:8000/wxapp/esp32/poll_commands/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "device_code=2025001&current_session=&status=idle"

# 测试轮询（采集状态）
curl -X POST http://localhost:8000/wxapp/esp32/poll_commands/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "device_code=2025001&current_session=1015&status=collecting"
```

### 2. 完整测试流程

```bash
# 1. 创建会话（模拟小程序操作）
curl -X POST http://localhost:8000/wxapp/start_session/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "openid=test_user&device_group_code=2025001"

# 2. 轮询获取开始指令
curl -X POST http://localhost:8000/wxapp/esp32/poll_commands/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "device_code=2025001&current_session=&status=idle"

# 3. 结束会话（模拟小程序操作）
curl -X POST http://localhost:8000/wxapp/end_session/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "session_id=1015"

# 4. 轮询获取停止指令
curl -X POST http://localhost:8000/wxapp/esp32/poll_commands/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "device_code=2025001&current_session=1015&status=collecting"
```

## ⚠️ 注意事项

### 1. 轮询间隔
- **建议间隔**: 3-5秒
- **不要过于频繁**: 避免给服务器造成压力
- **不要太慢**: 确保能及时获取指令

### 2. 错误处理
- **网络重连**: WiFi断开时自动重连
- **JSON解析**: 处理解析失败的情况
- **HTTP错误**: 处理网络请求失败

### 3. 状态同步
- **及时更新**: 收到指令后立即更新本地状态
- **状态确认**: 向服务器发送状态确认
- **会话跟踪**: 正确跟踪当前会话ID

### 4. 设备码一致性
- **确保一致**: ESP32的设备码必须与小程序中使用的设备码一致
- **默认设备码**: "2025001"

## 🔧 故障排除

### 1. 常见问题

**问题**: 轮询总是返回null
- **检查**: 确认设备码是否正确
- **检查**: 确认服务器是否有对应设备的会话

**问题**: 网络连接失败
- **检查**: WiFi配置是否正确
- **检查**: 服务器地址是否可访问

**问题**: JSON解析失败
- **检查**: 服务器响应格式是否正确
- **检查**: ArduinoJson库是否正确安装

### 2. 调试技巧

```cpp
// 启用详细调试信息
#define DEBUG_MODE 1

#ifdef DEBUG_MODE
  #define DEBUG_PRINT(x) Serial.print(x)
  #define DEBUG_PRINTLN(x) Serial.println(x)
#else
  #define DEBUG_PRINT(x)
  #define DEBUG_PRINTLN(x)
#endif
```

## 📚 相关文档

- [ESP32 API文档](./ESP32_API_DOCUMENTATION.md)
- [完整API指南](./COMPLETE_API_GUIDE.md)
- [部署指南](./DEPLOYMENT_GUIDE.md)

---

**最后更新**: 2025年8月5日  
**版本**: 1.0 