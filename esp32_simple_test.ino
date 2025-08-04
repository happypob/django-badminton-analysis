#include <WiFi.h>
#include <HTTPClient.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

// WiFi配置
const char* ssid = "111";
const char* password = "12345678";

// 设备配置
const char* device_code = "2025001";
const char* server_url = "http://47.122.129.159:8000";

// 测试会话ID (使用刚才创建的会话ID)
int test_session_id = 1011;

// 数据上传任务句柄
TaskHandle_t uploadTask = NULL;

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("🚀 ESP32-S3 简单测试程序");
    Serial.println("========================================");
    Serial.printf("设备码: %s\n", device_code);
    Serial.printf("服务器: %s\n", server_url);
    Serial.printf("测试会话ID: %d\n", test_session_id);
    Serial.println("========================================");
    
    // 连接WiFi
    connectWiFi();
    
    // 创建数据上传任务
    xTaskCreate(uploadTaskFunction, "UploadTask", 8192, NULL, 1, &uploadTask);
    
    Serial.println("✅ 系统初始化完成，开始自动上传测试数据");
}

void connectWiFi() {
    Serial.println("🔄 连接WiFi...");
    
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();
    delay(1000);
    
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
    }
}

void uploadTaskFunction(void* parameter) {
    Serial.println("📤 开始自动上传测试数据");
    
    int upload_count = 0;
    
    while (true) {
        if (WiFi.status() == WL_CONNECTED) {
            // 上传腰部传感器数据
            uploadSensorData("waist", upload_count);
            vTaskDelay(pdMS_TO_TICKS(3000));  // 3秒间隔
            
            // 上传肩部传感器数据
            uploadSensorData("shoulder", upload_count);
            vTaskDelay(pdMS_TO_TICKS(3000));  // 3秒间隔
            
            // 上传腕部传感器数据
            uploadSensorData("wrist", upload_count);
            vTaskDelay(pdMS_TO_TICKS(3000));  // 3秒间隔
            
            upload_count++;
            
            // 每10次上传打印一次状态
            if (upload_count % 10 == 0) {
                Serial.printf("📈 已上传 %d 组数据\n", upload_count * 3);
            }
        } else {
            Serial.println("❌ WiFi连接断开，等待重连...");
            vTaskDelay(pdMS_TO_TICKS(5000));
        }
    }
}

void uploadSensorData(const char* sensor_type, int count) {
    HTTPClient http;
    String url = String(server_url) + "/wxapp/esp32/upload/";
    http.begin(url);
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    
    // 生成模拟传感器数据
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
    postData += "&session_id=" + String(test_session_id);
    postData += "&timestamp=" + String(millis());
    
    Serial.printf("📡 上传 %s 数据 (第%d次)...\n", sensor_type, count + 1);
    
    int httpResponseCode = http.POST(postData);
    
    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.printf("✅ %s 上传成功 (HTTP: %d)\n", sensor_type, httpResponseCode);
        
        // 检查响应是否包含成功信息
        if (response.indexOf("ESP32 data upload success") != -1) {
            Serial.printf("🎉 %s 数据上传成功确认\n", sensor_type);
        }
    } else {
        Serial.printf("❌ %s 上传失败 (错误: %d)\n", sensor_type, httpResponseCode);
    }
    
    http.end();
}

void loop() {
    // 检查WiFi连接状态
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("⚠️ WiFi连接断开，尝试重连...");
        connectWiFi();
    }
    
    // 定期打印状态
    static unsigned long lastStatusPrint = 0;
    if (millis() - lastStatusPrint > 60000) {  // 每60秒打印一次
        Serial.println("=== 系统状态 ===");
        Serial.printf("设备码: %s\n", device_code);
        Serial.printf("WiFi状态: %s\n", WiFi.status() == WL_CONNECTED ? "已连接" : "未连接");
        Serial.printf("IP地址: %s\n", WiFi.localIP().toString().c_str());
        Serial.printf("信号强度: %d dBm\n", WiFi.RSSI());
        Serial.printf("运行时间: %lu ms\n", millis());
        Serial.println("================");
        lastStatusPrint = millis();
    }
    
    delay(1000);
} 