/*
 * ESP32 HTTP客户端
 * 用于跨网络与服务器通信
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// WiFi配置
const char* ssid = "111";           // 你的WiFi名称
const char* password = "12345678";   // 你的WiFi密码

// 服务器配置
const char* serverUrl = "http://你的服务器IP:8000";  // 替换为你的服务器IP
const int serverPort = 8000;

// 设备配置
const String deviceCode = "2025001";  // ESP32设备码

// 状态变量
bool isCollecting = false;
String currentSessionId = "";
unsigned long lastHeartbeat = 0;
const unsigned long heartbeatInterval = 5000; // 5秒心跳

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("🚀 ESP32 HTTP客户端启动");
  Serial.println("================================");
  
  // 连接WiFi
  connectToWiFi();
  
  Serial.println("✅ ESP32 HTTP客户端初始化完成");
  Serial.println("📡 准备与服务器通信...");
  Serial.println("================================");
}

void loop() {
  // 检查WiFi连接
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi连接断开，尝试重连...");
    connectToWiFi();
    return;
  }
  
  // 发送心跳（如果正在采集）
  if (isCollecting && millis() - lastHeartbeat > heartbeatInterval) {
    sendHeartbeat();
    lastHeartbeat = millis();
  }
  
  delay(1000); // 1秒延迟
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
    Serial.print("📄 响应: ");
    Serial.println(response);
  } else {
    Serial.print("❌ 心跳发送失败，错误码: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
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

// 手动触发开始采集（用于测试）
void manualStartCollection() {
  if (!isCollecting) {
    String testSessionId = "test_" + String(millis());
    startCollection(testSessionId);
  }
}

// 手动触发停止采集（用于测试）
void manualStopCollection() {
  if (isCollecting) {
    stopCollection(currentSessionId);
  }
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
  Serial.println("================================");
} 