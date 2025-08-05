/*
 * ESP32 HTTP轮询客户端
 * 用于跨网络与服务器通信
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// WiFi配置
const char* ssid = "111";           // 你的WiFi名称
const char* password = "12345678";   // 你的WiFi密码

// 服务器配置 - 替换为你的服务器公网IP
const char* serverUrl = "http://你的服务器公网IP:8000";  // 例如: http://123.456.789.123:8000
const int serverPort = 8000;

// 设备配置
const String deviceCode = "2025001";  // ESP32设备码

// 状态变量
bool isCollecting = false;
String currentSessionId = "";
unsigned long lastPolling = 0;
const unsigned long pollingInterval = 3000; // 3秒轮询一次
unsigned long lastHeartbeat = 0;
const unsigned long heartbeatInterval = 5000; // 5秒心跳

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("🚀 ESP32 HTTP轮询客户端启动");
  Serial.println("================================");
  
  // 连接WiFi
  connectToWiFi();
  
  Serial.println("✅ ESP32 HTTP轮询客户端初始化完成");
  Serial.println("📡 开始轮询服务器指令...");
  Serial.println("================================");
}

void loop() {
  // 检查WiFi连接
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi连接断开，尝试重连...");
    connectToWiFi();
    return;
  }
  
  // 定期轮询服务器指令
  if (millis() - lastPolling > pollingInterval) {
    pollServerCommands();
    lastPolling = millis();
  }
  
  // 发送心跳（如果正在采集）
  if (isCollecting && millis() - lastHeartbeat > heartbeatInterval) {
    sendHeartbeat();
    lastHeartbeat = millis();
  }
  
  delay(100); // 短暂延迟
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
    Serial.print("📡 设备码: ");
    Serial.println(deviceCode);
  } else {
    Serial.println();
    Serial.println("❌ WiFi连接失败!");
  }
}

void pollServerCommands() {
  HTTPClient http;
  String url = String(serverUrl) + "/wxapp/esp32/poll_commands/";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");
  
  // 发送轮询请求
  String postData = "device_code=" + deviceCode + 
                   "&current_session=" + currentSessionId + 
                   "&status=" + (isCollecting ? "collecting" : "idle");
  
  int httpResponseCode = http.POST(postData);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.print("📡 轮询响应 (");
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
  
  // 检查是否有新指令
  if (doc.containsKey("command")) {
    const char* command = doc["command"];
    const char* sessionId = doc["session_id"];
    
    Serial.println("📨 收到服务器指令:");
    Serial.print("   指令: ");
    Serial.println(command);
    Serial.print("   会话ID: ");
    Serial.println(sessionId);
    
    // 处理指令
    if (strcmp(command, "START_COLLECTION") == 0) {
      startCollection(String(sessionId));
    } else if (strcmp(command, "STOP_COLLECTION") == 0) {
      stopCollection(String(sessionId));
    }
  } else {
    Serial.println("📭 无新指令");
  }
}

void startCollection(String sessionId) {
  Serial.println("🟢 开始采集数据!");
  Serial.print("   会话ID: ");
  Serial.println(sessionId);
  
  isCollecting = true;
  currentSessionId = sessionId;
  lastHeartbeat = millis();
  
  // 发送开始采集确认
  sendCollectionStatus("START_COLLECTION_CONFIRMED", sessionId);
  
  Serial.println("📊 开始采集传感器数据...");
}

void stopCollection(String sessionId) {
  Serial.println("🔴 停止采集数据!");
  Serial.print("   会话ID: ");
  Serial.println(sessionId);
  
  isCollecting = false;
  currentSessionId = "";
  
  // 发送停止采集确认
  sendCollectionStatus("STOP_COLLECTION_CONFIRMED", sessionId);
  
  Serial.println("📊 停止采集传感器数据...");
}

void sendCollectionStatus(String status, String sessionId) {
  HTTPClient http;
  String url = String(serverUrl) + "/wxapp/esp32/status/";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");
  
  String postData = "status=" + status + 
                   "&session_id=" + sessionId + 
                   "&device_code=" + deviceCode;
  
  int httpResponseCode = http.POST(postData);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.print("📤 状态确认发送成功，响应码: ");
    Serial.println(httpResponseCode);
  } else {
    Serial.print("❌ 状态确认发送失败，错误码: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}

void sendHeartbeat() {
  if (!isCollecting) return;
  
  HTTPClient http;
  String url = String(serverUrl) + "/wxapp/esp32/heartbeat/";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");
  
  // 创建心跳数据
  String postData = "session_id=" + currentSessionId + 
                   "&device_code=" + deviceCode + 
                   "&status=collecting";
  
  int httpResponseCode = http.POST(postData);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.print("💓 心跳发送成功，响应码: ");
    Serial.println(httpResponseCode);
  } else {
    Serial.print("❌ 心跳发送失败，错误码: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}

// 获取当前状态信息
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
  Serial.print("   服务器: ");
  Serial.println(serverUrl);
  Serial.println("================================");
} 