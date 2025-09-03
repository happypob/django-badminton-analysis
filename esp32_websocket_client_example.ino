#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>

// WiFi配置
const char* ssid = "您的WiFi名称";           // 替换为您的WiFi名称
const char* password = "您的WiFi密码";       // 替换为您的WiFi密码

// WebSocket服务器配置
const char* websocket_server = "175.178.100.179";
const int websocket_port = 8000;
const char* websocket_path = "/ws/esp32/esp32s3_001/";  // 替换为您的设备编码

// 设备配置
const String device_code = "esp32s3_001";  // 替换为您的设备编码

// WebSocket客户端
WebSocketsClient webSocket;

// 状态变量
bool isConnected = false;
unsigned long lastHeartbeat = 0;
const unsigned long heartbeatInterval = 5000; // 5秒心跳间隔

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("🚀 ESP32 WebSocket客户端启动");
    Serial.println("================================");
    
    // 连接WiFi
    connectToWiFi();
    
    // 初始化WebSocket
    initWebSocket();
    
    Serial.println("✅ ESP32初始化完成");
    Serial.println("📡 准备连接WebSocket服务器...");
}

void loop() {
    // 处理WebSocket事件
    webSocket.loop();
    
    // 发送定期心跳
    if (isConnected && millis() - lastHeartbeat > heartbeatInterval) {
        sendHeartbeat();
        lastHeartbeat = millis();
    }
    
    // 模拟发送传感器数据
    static unsigned long lastSensorData = 0;
    if (isConnected && millis() - lastSensorData > 2000) { // 每2秒发送一次传感器数据
        sendSensorData();
        lastSensorData = millis();
    }
    
    delay(100);
}

void connectToWiFi() {
    Serial.print("📶 连接WiFi: ");
    Serial.println(ssid);
    
    WiFi.begin(ssid, password);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
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

void initWebSocket() {
    // 配置WebSocket连接
    webSocket.begin(websocket_server, websocket_port, websocket_path);
    
    // 设置事件回调
    webSocket.onEvent(webSocketEvent);
    
    // 设置重连间隔
    webSocket.setReconnectInterval(5000);
    
    Serial.print("🔌 WebSocket配置完成: ");
    Serial.print(websocket_server);
    Serial.print(":");
    Serial.print(websocket_port);
    Serial.println(websocket_path);
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
    switch(type) {
        case WStype_DISCONNECTED:
            Serial.println("❌ WebSocket连接断开");
            isConnected = false;
            break;
            
        case WStype_CONNECTED:
            Serial.printf("✅ WebSocket连接成功: %s\n", payload);
            isConnected = true;
            
            // 连接成功后发送初始状态
            sendStatusUpdate("ready");
            break;
            
        case WStype_TEXT:
            Serial.printf("📥 收到消息: %s\n", payload);
            handleMessage((char*)payload);
            break;
            
        case WStype_BIN:
            Serial.printf("📦 收到二进制数据: %u bytes\n", length);
            break;
            
        case WStype_ERROR:
            Serial.printf("❌ WebSocket错误: %s\n", payload);
            break;
            
        default:
            break;
    }
}

void handleMessage(const char* message) {
    // 解析JSON消息
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, message);
    
    String messageType = doc["type"];
    
    if (messageType == "connection_established") {
        Serial.println("🎉 服务器确认连接建立");
        
    } else if (messageType == "start_collection") {
        Serial.println("🟢 收到开始采集指令");
        sendStatusUpdate("collecting");
        
    } else if (messageType == "stop_collection") {
        Serial.println("🔴 收到停止采集指令");
        sendStatusUpdate("idle");
        
    } else if (messageType == "heartbeat_response") {
        Serial.println("💓 心跳响应正常");
        
    } else {
        Serial.println("❓ 未知消息类型: " + messageType);
    }
}

void sendHeartbeat() {
    if (!isConnected) return;
    
    DynamicJsonDocument doc(512);
    doc["type"] = "heartbeat";
    doc["device_code"] = device_code;
    doc["timestamp"] = millis();
    
    String message;
    serializeJson(doc, message);
    
    webSocket.sendTXT(message);
    Serial.println("💓 发送心跳");
}

void sendSensorData() {
    if (!isConnected) return;
    
    // 模拟传感器数据
    DynamicJsonDocument doc(1024);
    doc["type"] = "sensor_data";
    doc["device_code"] = device_code;
    doc["sensor_type"] = "waist";  // 腰部传感器
    
    // 模拟加速度计数据
    JsonArray acc = doc.createNestedArray("data").createNestedArray("acc");
    acc.add(random(-100, 100) / 10.0);  // X轴
    acc.add(random(-100, 100) / 10.0);  // Y轴
    acc.add(random(80, 120) / 10.0);    // Z轴（重力）
    
    // 模拟陀螺仪数据
    JsonArray gyro = doc["data"].createNestedArray("gyro");
    gyro.add(random(-50, 50) / 10.0);   // X轴角速度
    gyro.add(random(-50, 50) / 10.0);   // Y轴角速度
    gyro.add(random(-50, 50) / 10.0);   // Z轴角速度
    
    // 模拟角度数据
    JsonArray angle = doc["data"].createNestedArray("angle");
    angle.add(random(-180, 180));       // Roll
    angle.add(random(-90, 90));         // Pitch
    angle.add(random(0, 360));          // Yaw
    
    doc["timestamp"] = millis();
    
    String message;
    serializeJson(doc, message);
    
    webSocket.sendTXT(message);
    Serial.println("📊 发送传感器数据");
}

void sendStatusUpdate(const String& status) {
    if (!isConnected) return;
    
    DynamicJsonDocument doc(512);
    doc["type"] = "status_update";
    doc["device_code"] = device_code;
    doc["status"] = status;
    doc["timestamp"] = millis();
    
    String message;
    serializeJson(doc, message);
    
    webSocket.sendTXT(message);
    Serial.println("📢 发送状态更新: " + status);
}

void sendBatchSensorData() {
    if (!isConnected) return;
    
    DynamicJsonDocument doc(2048);
    doc["type"] = "batch_sensor_data";
    doc["device_code"] = device_code;
    doc["sensor_type"] = "waist";
    
    JsonArray dataArray = doc.createNestedArray("data");
    
    // 发送5条传感器数据
    for (int i = 0; i < 5; i++) {
        JsonObject dataPoint = dataArray.createNestedObject();
        
        JsonArray acc = dataPoint.createNestedArray("acc");
        acc.add(random(-100, 100) / 10.0);
        acc.add(random(-100, 100) / 10.0);
        acc.add(random(80, 120) / 10.0);
        
        JsonArray gyro = dataPoint.createNestedArray("gyro");
        gyro.add(random(-50, 50) / 10.0);
        gyro.add(random(-50, 50) / 10.0);
        gyro.add(random(-50, 50) / 10.0);
        
        JsonArray angle = dataPoint.createNestedArray("angle");
        angle.add(random(-180, 180));
        angle.add(random(-90, 90));
        angle.add(random(0, 360));
        
        dataPoint["timestamp"] = millis() + i * 10;
    }
    
    String message;
    serializeJson(doc, message);
    
    webSocket.sendTXT(message);
    Serial.println("📦 发送批量传感器数据");
} 