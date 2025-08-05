/*
 * ESP32 UDP广播监听器
 * 用于监听服务器发送的UDP广播消息
 */

#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>

// WiFi配置
const char* ssid = "111";           // 你的WiFi名称
const char* password = "12345678";   // 你的WiFi密码

// UDP配置
const int udpPort = 8888;
WiFiUDP udp;

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
  
  Serial.println("🚀 ESP32 UDP广播监听器启动");
  Serial.println("================================");
  
  // 连接WiFi
  connectToWiFi();
  
  // 启动UDP监听
  startUDPListener();
  
  Serial.println("✅ ESP32 UDP监听器初始化完成");
  Serial.println("📡 正在监听UDP广播消息...");
  Serial.println("================================");
}

void loop() {
  // 检查WiFi连接
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi连接断开，尝试重连...");
    connectToWiFi();
    return;
  }
  
  // 处理UDP消息
  handleUDPMessages();
  
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

void startUDPListener() {
  if (udp.begin(udpPort)) {
    Serial.print("✅ UDP监听器启动成功，端口: ");
    Serial.println(udpPort);
  } else {
    Serial.println("❌ UDP监听器启动失败!");
  }
}

void handleUDPMessages() {
  int packetSize = udp.parsePacket();
  if (packetSize) {
    // 读取UDP数据
    char incomingPacket[255];
    int len = udp.read(incomingPacket, 255);
    if (len > 0) {
      incomingPacket[len] = 0;
    }
    
    // 显示接收信息
    Serial.println();
    Serial.println("📨 收到UDP广播消息:");
    Serial.print("📡 来源: ");
    Serial.print(udp.remoteIP());
    Serial.print(":");
    Serial.println(udp.remotePort());
    Serial.print("📦 数据长度: ");
    Serial.print(len);
    Serial.println(" 字节");
    Serial.print("📄 原始数据: ");
    Serial.println(incomingPacket);
    
    // 解析JSON消息
    parseUDPMessage(incomingPacket);
  }
}

void parseUDPMessage(const char* message) {
  DynamicJsonDocument doc(512);
  DeserializationError error = deserializeJson(doc, message);
  
  if (error) {
    Serial.println("❌ JSON解析失败:");
    Serial.println(error.c_str());
    return;
  }
  
  // 解析消息内容
  const char* command = doc["command"];
  const char* sessionId = doc["session_id"];
  const char* deviceCodeMsg = doc["device_code"];
  const char* timestamp = doc["timestamp"];
  
  Serial.println("📋 解析的JSON数据:");
  Serial.print("   指令: ");
  Serial.println(command);
  Serial.print("   会话ID: ");
  Serial.println(sessionId);
  Serial.print("   设备码: ");
  Serial.println(deviceCodeMsg);
  Serial.print("   时间戳: ");
  Serial.println(timestamp);
  
  // 检查设备码是否匹配
  if (strcmp(deviceCodeMsg, deviceCode.c_str()) != 0) {
    Serial.println("⚠️  设备码不匹配，忽略此消息");
    return;
  }
  
  // 处理指令
  if (strcmp(command, "START_COLLECTION") == 0) {
    handleStartCollection(sessionId);
  } else if (strcmp(command, "STOP_COLLECTION") == 0) {
    handleStopCollection(sessionId);
  } else {
    Serial.print("❓ 未知指令: ");
    Serial.println(command);
  }
}

void handleStartCollection(const char* sessionId) {
  Serial.println("🟢 收到开始采集指令!");
  Serial.print("   会话ID: ");
  Serial.println(sessionId);
  
  isCollecting = true;
  currentSessionId = String(sessionId);
  lastHeartbeat = millis();
  
  // 这里可以添加实际的传感器数据采集代码
  Serial.println("📊 开始采集传感器数据...");
  
  // 发送确认消息
  sendConfirmation("START_COLLECTION_CONFIRMED", sessionId);
}

void handleStopCollection(const char* sessionId) {
  Serial.println("🔴 收到停止采集指令!");
  Serial.print("   会话ID: ");
  Serial.println(sessionId);
  
  isCollecting = false;
  currentSessionId = "";
  
  // 这里可以添加停止采集的代码
  Serial.println("📊 停止采集传感器数据...");
  
  // 发送确认消息
  sendConfirmation("STOP_COLLECTION_CONFIRMED", sessionId);
}

void sendConfirmation(const char* status, const char* sessionId) {
  // 创建确认消息
  DynamicJsonDocument doc(256);
  doc["status"] = status;
  doc["session_id"] = sessionId;
  doc["device_code"] = deviceCode;
  doc["timestamp"] = String(millis());
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  // 发送确认消息（这里可以发送到服务器）
  Serial.print("📤 发送确认消息: ");
  Serial.println(jsonString);
}

void sendHeartbeat() {
  if (!isCollecting) return;
  
  // 创建心跳消息
  DynamicJsonDocument doc(256);
  doc["type"] = "HEARTBEAT";
  doc["session_id"] = currentSessionId;
  doc["device_code"] = deviceCode;
  doc["timestamp"] = String(millis());
  doc["status"] = "collecting";
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.print("💓 发送心跳: ");
  Serial.println(jsonString);
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