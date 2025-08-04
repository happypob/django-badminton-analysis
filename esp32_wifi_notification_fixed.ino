#include <WiFi.h>
#include <HTTPClient.h>
#include <WebServer.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <ArduinoJson.h>

// 函数前置声明
void connectWiFi();
void setupWebServer();
void registerDeviceIP();
void handleStartCollection();
void handleStopCollection();
void handleStatus();
void dataUploadTaskFunction(void* parameter);
void uploadSensorData(const char* sensor_type);
void printSystemStatus();

// WiFi配置
const char* ssid = "111";
const char* password = "12345678";

// 设备配置
const char* device_code = "2025001";
const char* server_url = "http://47.122.129.159:8000";

// Web服务器
WebServer server(80);

// 数据采集控制
bool is_collecting = false;
int current_session_id = 0;
unsigned long last_upload_time = 0;
int upload_count = 0;

// FreeRTOS任务句柄
TaskHandle_t dataUploadTask = NULL;

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("🚀 ESP32-S3 羽毛球传感器数据采集系统");
    Serial.println("========================================");
    Serial.printf("设备码: %s\n", device_code);
    Serial.printf("服务器: %s\n", server_url);
    Serial.println("========================================");
    
    // 连接WiFi
    connectWiFi();
    
    // 启动Web服务器
    setupWebServer();
    
    // 注册设备IP到服务器
    registerDeviceIP();
    
    Serial.println("✅ 系统初始化完成");
    printSystemStatus();
}

void connectWiFi() {
    Serial.println("🔄 连接WiFi...");
    
    // 设置WiFi模式为Station模式
    WiFi.mode(WIFI_STA);
    
    // 清除之前的连接
    WiFi.disconnect();
    delay(1000);
    
    // 开始连接
    WiFi.begin(ssid, password);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(1000);
        attempts++;
        Serial.printf("连接中... %d/20\n", attempts);
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("✅ WiFi连接成功!");
        Serial.printf("IP地址: %s\n", WiFi.localIP().toString().c_str());
        Serial.printf("信号强度: %d dBm\n", WiFi.RSSI());
    } else {
        Serial.println("❌ WiFi连接失败!");
        Serial.printf("WiFi状态: %d\n", WiFi.status());
    }
}

void setupWebServer() {
    // 设置Web服务器路由
    server.on("/start_collection", HTTP_POST, handleStartCollection);
    server.on("/stop_collection", HTTP_POST, handleStopCollection);
    server.on("/status", HTTP_GET, handleStatus);
    
    server.begin();
    Serial.println("🌐 Web服务器已启动 (端口80)");
    Serial.printf("本地访问地址: http://%s\n", WiFi.localIP().toString().c_str());
}

void registerDeviceIP() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("❌ WiFi未连接，无法注册IP");
        return;
    }
    
    HTTPClient http;
    String url = String(server_url) + "/wxapp/register_device_ip/";
    http.begin(url);
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    
    String postData = "device_code=" + String(device_code);
    postData += "&ip_address=" + WiFi.localIP().toString();
    
    Serial.println("📝 注册设备IP到服务器...");
    Serial.printf("URL: %s\n", url.c_str());
    Serial.printf("数据: %s\n", postData.c_str());
    
    int httpResponseCode = http.POST(postData);
    
    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.printf("✅ 设备IP注册成功 (HTTP: %d)\n", httpResponseCode);
        Serial.printf("响应: %s\n", response.c_str());
    } else {
        Serial.printf("❌ 设备IP注册失败 (错误: %d)\n", httpResponseCode);
    }
    
    http.end();
}

void handleStartCollection() {
    Serial.println("📡 收到开始采集通知");
    
    if (server.hasArg("session_id") && server.hasArg("device_code")) {
        String sessionId = server.arg("session_id");
        String deviceCode = server.arg("device_code");
        
        Serial.printf("会话ID: %s\n", sessionId.c_str());
        Serial.printf("设备码: %s\n", deviceCode.c_str());
        
        // 开始数据采集
        current_session_id = sessionId.toInt();
        is_collecting = true;
        upload_count = 0;
        last_upload_time = millis();
        
        // 创建数据上传任务
        if (dataUploadTask == NULL) {
            xTaskCreate(dataUploadTaskFunction, "DataUpload", 8192, NULL, 1, &dataUploadTask);
            Serial.println("✅ 数据上传任务已创建");
        }
        
        // 返回成功响应
        String response = "{";
        response += "\"status\":\"collection_started\",";
        response += "\"session_id\":" + sessionId + ",";
        response += "\"device_code\":\"" + String(device_code) + "\"";
        response += "}";
        
        server.send(200, "application/json", response);
        
        Serial.println("✅ 数据采集已开始");
        printSystemStatus();
    } else {
        server.send(400, "text/plain", "Missing parameters");
        Serial.println("❌ 参数缺失");
    }
}

void handleStopCollection() {
    Serial.println("📡 收到停止采集通知");
    
    if (server.hasArg("device_code")) {
        String deviceCode = server.arg("device_code");
        Serial.printf("设备码: %s\n", deviceCode.c_str());
        
        // 停止数据采集
        is_collecting = false;
        current_session_id = 0;
        
        // 删除数据上传任务
        if (dataUploadTask != NULL) {
            vTaskDelete(dataUploadTask);
            dataUploadTask = NULL;
            Serial.println("✅ 数据上传任务已停止");
        }
        
        // 返回成功响应
        String response = "{";
        response += "\"status\":\"collection_stopped\",";
        response += "\"device_code\":\"" + String(device_code) + "\",";
        response += "\"total_uploads\":" + String(upload_count);
        response += "}";
        
        server.send(200, "application/json", response);
        
        Serial.println("✅ 数据采集已停止");
        printSystemStatus();
    } else {
        server.send(400, "text/plain", "Missing device_code");
        Serial.println("❌ 设备码参数缺失");
    }
}

void handleStatus() {
    String status = "{";
    status += "\"device_code\":\"" + String(device_code) + "\",";
    status += "\"ip_address\":\"" + WiFi.localIP().toString() + "\",";
    
    // WiFi状态
    String wifiStatus = (WiFi.status() == WL_CONNECTED) ? "connected" : "disconnected";
    status += "\"wifi_status\":\"" + wifiStatus + "\",";
    
    // 采集状态
    String collectingStatus = is_collecting ? "true" : "false";
    status += "\"is_collecting\":" + collectingStatus + ",";
    
    status += "\"session_id\":" + String(current_session_id) + ",";
    status += "\"signal_strength\":" + String(WiFi.RSSI()) + ",";
    status += "\"upload_count\":" + String(upload_count) + ",";
    status += "\"uptime\":" + String(millis());
    status += "}";
    
    server.send(200, "application/json", status);
    Serial.println("📊 状态信息已返回");
}

void dataUploadTaskFunction(void* parameter) {
    Serial.println("📤 数据上传任务启动");
    
    while (is_collecting) {
        // 上传腰部传感器数据
        uploadSensorData("waist");
        vTaskDelay(pdMS_TO_TICKS(2000));  // 2秒间隔
        
        // 上传肩部传感器数据
        uploadSensorData("shoulder");
        vTaskDelay(pdMS_TO_TICKS(2000));  // 2秒间隔
        
        // 上传腕部传感器数据
        uploadSensorData("wrist");
        vTaskDelay(pdMS_TO_TICKS(2000));  // 2秒间隔
        
        // 每10次上传打印一次状态
        if (upload_count % 10 == 0 && upload_count > 0) {
            Serial.printf("📈 已上传 %d 组数据\n", upload_count);
        }
    }
    
    Serial.println("🛑 数据上传任务结束");
    vTaskDelete(NULL);
}

void uploadSensorData(const char* sensor_type) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("❌ WiFi未连接，跳过上传");
        return;
    }
    
    if (current_session_id == 0) {
        Serial.println("❌ 无效的会话ID，跳过上传");
        return;
    }
    
    HTTPClient http;
    String url = String(server_url) + "/wxapp/esp32/upload/";
    http.begin(url);
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    
    // 生成模拟传感器数据 - 更真实的数据
    float acc[3] = {
        1.2f + random(-10, 10) * 0.1f, 
        0.8f + random(-10, 10) * 0.1f, 
        9.8f + random(-10, 10) * 0.1f
    };
    float gyro[3] = {
        0.1f + random(-10, 10) * 0.01f, 
        0.2f + random(-10, 10) * 0.01f, 
        0.3f + random(-10, 10) * 0.01f
    };
    float angle[3] = {
        45.0f + random(-15, 15), 
        30.0f + random(-15, 15), 
        60.0f + random(-15, 15)
    };
    
    // 构建JSON数据
    String jsonData = "{";
    jsonData += "\"acc\":[" + String(acc[0], 2) + "," + String(acc[1], 2) + "," + String(acc[2], 2) + "],";
    jsonData += "\"gyro\":[" + String(gyro[0], 2) + "," + String(gyro[1], 2) + "," + String(gyro[2], 2) + "],";
    jsonData += "\"angle\":[" + String(angle[0], 1) + "," + String(angle[1], 1) + "," + String(angle[2], 1) + "]";
    jsonData += "}";
    
    // 构建POST数据
    String postData = "device_code=" + String(device_code);
    postData += "&sensor_type=" + String(sensor_type);
    postData += "&data=" + jsonData;
    postData += "&session_id=" + String(current_session_id);
    postData += "&timestamp=" + String(millis());
    
    Serial.printf("📡 上传 %s 数据 (会话ID: %d)...\n", sensor_type, current_session_id);
    
    int httpResponseCode = http.POST(postData);
    
    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.printf("✅ %s 上传成功 (HTTP: %d)\n", sensor_type, httpResponseCode);
        
        // 尝试解析响应
        if (response.indexOf("ESP32 data upload success") != -1) {
            upload_count++;
            last_upload_time = millis();
        }
    } else {
        Serial.printf("❌ %s 上传失败 (错误: %d)\n", sensor_type, httpResponseCode);
    }
    
    http.end();
}

void printSystemStatus() {
    Serial.println("=== 系统状态 ===");
    Serial.printf("设备码: %s\n", device_code);
    Serial.printf("WiFi状态: %s\n", WiFi.status() == WL_CONNECTED ? "已连接" : "未连接");
    Serial.printf("IP地址: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("信号强度: %d dBm\n", WiFi.RSSI());
    Serial.printf("数据采集: %s\n", is_collecting ? "进行中" : "已停止");
    Serial.printf("会话ID: %d\n", current_session_id);
    Serial.printf("上传次数: %d\n", upload_count);
    Serial.printf("运行时间: %lu ms\n", millis());
    Serial.println("================");
}

void loop() {
    // 处理Web服务器请求
    server.handleClient();
    
    // 检查WiFi连接状态
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("⚠️ WiFi连接断开，尝试重连...");
        connectWiFi();
        if (WiFi.status() == WL_CONNECTED) {
            registerDeviceIP();  // 重新注册IP
        }
    }
    
    // 定期打印状态
    static unsigned long lastStatusPrint = 0;
    if (millis() - lastStatusPrint > 60000) {  // 每60秒打印一次
        printSystemStatus();
        lastStatusPrint = millis();
    }
    
    // 如果正在采集但长时间没有上传，重新启动任务
    if (is_collecting && (millis() - last_upload_time > 30000) && last_upload_time > 0) {
        Serial.println("⚠️ 检测到上传任务可能卡住，重新启动...");
        if (dataUploadTask != NULL) {
            vTaskDelete(dataUploadTask);
            dataUploadTask = NULL;
        }
        xTaskCreate(dataUploadTaskFunction, "DataUpload", 8192, NULL, 1, &dataUploadTask);
        last_upload_time = millis();
    }
    
    delay(1000);
} 