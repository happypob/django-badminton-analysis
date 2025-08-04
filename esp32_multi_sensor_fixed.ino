#include <WiFi.h>
#include <HTTPClient.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>

// WiFi配置
const char* ssid = "111";
const char* password = "12345678";

// 服务器配置
const char* server_url = "http://47.122.129.159:8000/wxapp/esp32/upload/";

// 设备配置
const char* device_code = "esp32_multi_001";
const int session_id = 123;  // 使用测试会话ID

// FreeRTOS队列
QueueHandle_t dataQueue;

// 数据结构
struct SensorData {
    String sensor_type;
    float acc[3];
    float gyro[3];
    float angle[3];
    unsigned long timestamp;
};

// WiFi连接函数 - 改进版本
bool connectWiFi() {
    Serial.println("🔄 开始连接WiFi...");
    Serial.printf("SSID: %s\n", ssid);
    
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    
    int attempts = 0;
    const int max_attempts = 20;
    
    while (WiFi.status() != WL_CONNECTED && attempts < max_attempts) {
        attempts++;
        Serial.printf("连接WiFi中... 尝试 %d/%d\n", attempts, max_attempts);
        delay(1000);
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("✅ WiFi连接成功!");
        Serial.printf("IP地址: %s\n", WiFi.localIP().toString().c_str());
        Serial.printf("信号强度: %d dBm\n", WiFi.RSSI());
        return true;
    } else {
        Serial.println("❌ WiFi连接失败!");
        Serial.printf("状态码: %d\n", WiFi.status());
        return false;
    }
}

// 构建JSON数据
String buildJsonData(float acc[3], float gyro[3], float angle[3]) {
    String jsonData = "{";
    jsonData += "\"acc\":[" + String(acc[0], 2) + "," + String(acc[1], 2) + "," + String(acc[2], 2) + "],";
    jsonData += "\"gyro\":[" + String(gyro[0], 2) + "," + String(gyro[1], 2) + "," + String(gyro[2], 2) + "],";
    jsonData += "\"angle\":[" + String(angle[0], 1) + "," + String(angle[1], 1) + "," + String(angle[2], 1) + "]";
    jsonData += "}";
    return jsonData;
}

// 上传传感器数据
bool uploadSensorData(const char* sensor_type, float acc[3], float gyro[3], float angle[3]) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("⚠️ WiFi未连接，无法上传数据");
        return false;
    }
    
    HTTPClient http;
    http.begin(server_url);
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    
    String jsonData = buildJsonData(acc, gyro, angle);
    
    String postData = "device_code=" + String(device_code);
    postData += "&sensor_type=" + String(sensor_type);
    postData += "&data=" + jsonData;
    postData += "&session_id=" + String(session_id);
    postData += "&timestamp=" + String(millis());
    
    Serial.printf("📡 上传 %s 数据...\n", sensor_type);
    Serial.printf("数据: %s\n", jsonData.c_str());
    
    int httpResponseCode = http.POST(postData);
    
    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.printf("✅ %s 上传成功 (状态码: %d)\n", sensor_type, httpResponseCode);
        Serial.printf("响应: %s\n", response.c_str());
        http.end();
        return true;
    } else {
        Serial.printf("❌ %s 上传失败 (错误码: %d)\n", sensor_type, httpResponseCode);
        Serial.printf("错误: %s\n", http.errorToString(httpResponseCode).c_str());
        http.end();
        return false;
    }
}

// 腰部传感器任务
void waistSensorTask(void* parameter) {
    Serial.println(" 腰部传感器任务启动");
    
    while (true) {
        // 模拟腰部传感器数据
        float acc[3] = {1.2 + random(-10, 10) * 0.1, 0.8 + random(-10, 10) * 0.1, 9.8 + random(-10, 10) * 0.1};
        float gyro[3] = {0.1 + random(-10, 10) * 0.01, 0.2 + random(-10, 10) * 0.01, 0.3 + random(-10, 10) * 0.01};
        float angle[3] = {45.0 + random(-10, 10), 30.0 + random(-10, 10), 60.0 + random(-10, 10)};
        
        // 创建传感器数据结构
        SensorData data;
        data.sensor_type = "waist";
        memcpy(data.acc, acc, sizeof(acc));
        memcpy(data.gyro, gyro, sizeof(gyro));
        memcpy(data.angle, angle, sizeof(angle));
        data.timestamp = millis();
        
        // 发送到队列
        if (xQueueSend(dataQueue, &data, pdMS_TO_TICKS(100)) != pdTRUE) {
            Serial.println("⚠️ 队列已满，丢弃腰部传感器数据");
        }
        
        vTaskDelay(pdMS_TO_TICKS(100));  // 100ms间隔
    }
}

// 肩部传感器任务
void shoulderSensorTask(void* parameter) {
    Serial.println(" 肩部传感器任务启动");
    
    while (true) {
        // 模拟肩部传感器数据
        float acc[3] = {1.5 + random(-10, 10) * 0.1, 1.0 + random(-10, 10) * 0.1, 9.8 + random(-10, 10) * 0.1};
        float gyro[3] = {0.2 + random(-10, 10) * 0.01, 0.3 + random(-10, 10) * 0.01, 0.4 + random(-10, 10) * 0.01};
        float angle[3] = {50.0 + random(-10, 10), 35.0 + random(-10, 10), 65.0 + random(-10, 10)};
        
        // 创建传感器数据结构
        SensorData data;
        data.sensor_type = "shoulder";
        memcpy(data.acc, acc, sizeof(acc));
        memcpy(data.gyro, gyro, sizeof(gyro));
        memcpy(data.angle, angle, sizeof(angle));
        data.timestamp = millis();
        
        // 发送到队列
        if (xQueueSend(dataQueue, &data, pdMS_TO_TICKS(100)) != pdTRUE) {
            Serial.println("⚠️ 队列已满，丢弃肩部传感器数据");
        }
        
        vTaskDelay(pdMS_TO_TICKS(120));  // 120ms间隔
    }
}

// 腕部传感器任务
void wristSensorTask(void* parameter) {
    Serial.println(" 腕部传感器任务启动");
    
    while (true) {
        // 模拟腕部传感器数据
        float acc[3] = {2.0 + random(-10, 10) * 0.1, 1.5 + random(-10, 10) * 0.1, 9.8 + random(-10, 10) * 0.1};
        float gyro[3] = {0.3 + random(-10, 10) * 0.01, 0.4 + random(-10, 10) * 0.01, 0.5 + random(-10, 10) * 0.01};
        float angle[3] = {55.0 + random(-10, 10), 40.0 + random(-10, 10), 70.0 + random(-10, 10)};
        
        // 创建传感器数据结构
        SensorData data;
        data.sensor_type = "wrist";
        memcpy(data.acc, acc, sizeof(acc));
        memcpy(data.gyro, gyro, sizeof(gyro));
        memcpy(data.angle, angle, sizeof(angle));
        data.timestamp = millis();
        
        // 发送到队列
        if (xQueueSend(dataQueue, &data, pdMS_TO_TICKS(100)) != pdTRUE) {
            Serial.println("⚠️ 队列已满，丢弃腕部传感器数据");
        }
        
        vTaskDelay(pdMS_TO_TICKS(150));  // 150ms间隔
    }
}

// 数据上传任务
void dataUploadTask(void* parameter) {
    Serial.println("📤 数据上传任务启动");
    
    while (true) {
        SensorData data;
        
        // 从队列接收数据
        if (xQueueReceive(dataQueue, &data, pdMS_TO_TICKS(1000)) == pdTRUE) {
            // 上传数据
            bool success = uploadSensorData(data.sensor_type.c_str(), data.acc, data.gyro, data.angle);
            
            if (success) {
                Serial.printf("✅ %s 数据上传成功\n", data.sensor_type.c_str());
            } else {
                Serial.printf("❌ %s 数据上传失败\n", data.sensor_type.c_str());
            }
        }
        
        vTaskDelay(pdMS_TO_TICKS(200));  // 200ms间隔
    }
}

// 状态监控任务
void statusMonitorTask(void* parameter) {
    Serial.println("📊 状态监控任务启动");
    
    while (true) {
        Serial.println("=== 系统状态 ===");
        Serial.printf("WiFi状态: %s\n", WiFi.status() == WL_CONNECTED ? "已连接" : "未连接");
        Serial.printf("WiFi信号强度: %d dBm\n", WiFi.RSSI());
        Serial.printf("可用堆内存: %d bytes\n", ESP.getFreeHeap());
        Serial.printf("任务运行时间: %lu ms\n", millis());
        Serial.println("================");
        
        vTaskDelay(pdMS_TO_TICKS(10000));  // 10秒间隔
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("\n🚀 ESP32多传感器数据上传系统启动");
    Serial.println("==================================");
    
    // 创建数据队列
    dataQueue = xQueueCreate(20, sizeof(SensorData));
    if (dataQueue == NULL) {
        Serial.println("❌ 队列创建失败!");
        return;
    }
    
    // 连接WiFi
    if (!connectWiFi()) {
        Serial.println("⚠️ WiFi连接失败，系统将继续尝试重连");
    }
    
    // 创建FreeRTOS任务
    xTaskCreate(waistSensorTask, "WaistSensor", 4096, NULL, 1, NULL);
    xTaskCreate(shoulderSensorTask, "ShoulderSensor", 4096, NULL, 1, NULL);
    xTaskCreate(wristSensorTask, "WristSensor", 4096, NULL, 1, NULL);
    xTaskCreate(dataUploadTask, "DataUpload", 8192, NULL, 2, NULL);
    xTaskCreate(statusMonitorTask, "StatusMonitor", 4096, NULL, 1, NULL);
    
    Serial.println("✅ 所有任务已创建");
    Serial.println("📡 开始多传感器数据上传...");
}

void loop() {
    // 主循环 - 处理WiFi重连
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("⚠️ WiFi连接断开，尝试重连...");
        if (connectWiFi()) {
            Serial.println("✅ WiFi重连成功!");
        } else {
            Serial.println("❌ WiFi重连失败!");
        }
    }
    
    delay(5000);  // 5秒检查一次
} 