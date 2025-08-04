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
const char* device_code = "esp32s3_multi_001";
const int session_id = 123;

// 数据收集控制
const unsigned long COLLECTION_DURATION = 30000;  // 30秒数据收集
unsigned long collection_start_time = 0;
bool collection_completed = false;

// 简化的JSON构建函数
String buildJsonData(float acc[3], float gyro[3], float angle[3]) {
    char jsonBuffer[256];
    snprintf(jsonBuffer, sizeof(jsonBuffer), 
        "{\"acc\":[%.2f,%.2f,%.2f],\"gyro\":[%.2f,%.2f,%.2f],\"angle\":[%.1f,%.1f,%.1f]}",
        acc[0], acc[1], acc[2],
        gyro[0], gyro[1], gyro[2],
        angle[0], angle[1], angle[2]
    );
    return String(jsonBuffer);
}

// 数据上传函数
bool uploadSensorData(const char* sensor_type, float acc[3], float gyro[3], float angle[3]) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("⚠️ WiFi未连接");
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
    
    int httpResponseCode = http.POST(postData);
    
    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.printf("✅ %s 上传成功 (HTTP: %d)\n", sensor_type, httpResponseCode);
        http.end();
        return true;
    } else {
        Serial.printf("❌ %s 上传失败 (错误: %d)\n", sensor_type, httpResponseCode);
        http.end();
        return false;
    }
}

// 腰部传感器任务
void waistSensorTask(void* parameter) {
    Serial.println(" 腰部传感器任务启动");
    
    while (!collection_completed) {
        // 模拟数据
        float acc[3] = {1.2 + random(-5, 5) * 0.1, 0.8 + random(-5, 5) * 0.1, 9.8 + random(-5, 5) * 0.1};
        float gyro[3] = {0.1 + random(-5, 5) * 0.01, 0.2 + random(-5, 5) * 0.01, 0.3 + random(-5, 5) * 0.01};
        float angle[3] = {45.0 + random(-5, 5), 30.0 + random(-5, 5), 60.0 + random(-5, 5)};
        
        uploadSensorData("waist", acc, gyro, angle);
        
        vTaskDelay(pdMS_TO_TICKS(1000));  // 1秒间隔
    }
    
    Serial.println("🛑 腰部传感器任务结束");
    vTaskDelete(NULL);
}

// 肩部传感器任务
void shoulderSensorTask(void* parameter) {
    Serial.println(" 肩部传感器任务启动");
    
    while (!collection_completed) {
        // 模拟数据
        float acc[3] = {1.5 + random(-5, 5) * 0.1, 1.0 + random(-5, 5) * 0.1, 9.8 + random(-5, 5) * 0.1};
        float gyro[3] = {0.2 + random(-5, 5) * 0.01, 0.3 + random(-5, 5) * 0.01, 0.4 + random(-5, 5) * 0.01};
        float angle[3] = {50.0 + random(-5, 5), 35.0 + random(-5, 5), 65.0 + random(-5, 5)};
        
        uploadSensorData("shoulder", acc, gyro, angle);
        
        vTaskDelay(pdMS_TO_TICKS(1200));  // 1.2秒间隔
    }
    
    Serial.println("🛑 肩部传感器任务结束");
    vTaskDelete(NULL);
}

// 腕部传感器任务
void wristSensorTask(void* parameter) {
    Serial.println(" 腕部传感器任务启动");
    
    while (!collection_completed) {
        // 模拟数据
        float acc[3] = {2.0 + random(-5, 5) * 0.1, 1.5 + random(-5, 5) * 0.1, 9.8 + random(-5, 5) * 0.1};
        float gyro[3] = {0.3 + random(-5, 5) * 0.01, 0.4 + random(-5, 5) * 0.01, 0.5 + random(-5, 5) * 0.01};
        float angle[3] = {55.0 + random(-5, 5), 40.0 + random(-5, 5), 70.0 + random(-5, 5)};
        
        uploadSensorData("wrist", acc, gyro, angle);
        
        vTaskDelay(pdMS_TO_TICKS(1500));  // 1.5秒间隔
    }
    
    Serial.println("🛑 腕部传感器任务结束");
    vTaskDelete(NULL);
}

// 数据收集控制任务
void collectionControlTask(void* parameter) {
    Serial.println("⏱️ 数据收集控制任务启动");
    
    collection_start_time = millis();
    Serial.printf("📊 开始数据收集，持续时间: %lu 毫秒\n", COLLECTION_DURATION);
    
    while (millis() - collection_start_time < COLLECTION_DURATION) {
        unsigned long elapsed = millis() - collection_start_time;
        unsigned long remaining = COLLECTION_DURATION - elapsed;
        
        Serial.printf("⏳ 数据收集中... 剩余时间: %lu 秒\n", remaining / 1000);
        
        vTaskDelay(pdMS_TO_TICKS(5000));  // 每5秒报告一次
    }
    
    // 数据收集完成
    collection_completed = true;
    Serial.println("✅ 数据收集完成！");
    
    // 通知服务器数据收集完成
    notifyCollectionComplete();
    
    vTaskDelete(NULL);
}

// 通知服务器数据收集完成
void notifyCollectionComplete() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("⚠️ WiFi未连接，无法通知服务器");
        return;
    }
    
    HTTPClient http;
    String mark_complete_url = "http://47.122.129.159:8000/wxapp/mark_complete/";
    http.begin(mark_complete_url);
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    
    String postData = "session_id=" + String(session_id);
    postData += "&completion_code=DATA_COLLECTION_COMPLETE_2024";
    
    Serial.println("📤 通知服务器数据收集完成...");
    Serial.printf("请求URL: %s\n", mark_complete_url.c_str());
    Serial.printf("请求数据: %s\n", postData.c_str());
    
    int httpResponseCode = http.POST(postData);
    
    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.printf("✅ 服务器通知成功 (HTTP: %d)\n", httpResponseCode);
        Serial.printf("响应: %s\n", response.c_str());
        
        // 解析响应数据
        if (response.indexOf("analysis_triggered") != -1) {
            Serial.println("🎯 数据分析已触发!");
        }
    } else {
        Serial.printf("❌ 服务器通知失败 (错误: %d)\n", httpResponseCode);
        Serial.printf("错误信息: %s\n", http.errorToString(httpResponseCode).c_str());
    }
    
    http.end();
}

// 状态监控任务
void statusMonitorTask(void* parameter) {
    Serial.println("📊 状态监控任务启动");
    
    while (!collection_completed) {
        Serial.println("=== 系统状态 ===");
        Serial.printf("WiFi状态: %s\n", WiFi.status() == WL_CONNECTED ? "已连接" : "未连接");
        Serial.printf("WiFi信号强度: %d dBm\n", WiFi.RSSI());
        Serial.printf("可用堆内存: %d bytes\n", ESP.getFreeHeap());
        Serial.printf("数据收集进度: %lu/%lu ms\n", millis() - collection_start_time, COLLECTION_DURATION);
        Serial.println("================");
        
        vTaskDelay(pdMS_TO_TICKS(10000));  // 10秒间隔
    }
    
    Serial.println("🛑 状态监控任务结束");
    vTaskDelete(NULL);
}

// WiFi连接函数
bool connectWiFi() {
    Serial.println("🔄 开始连接WiFi...");
    
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
        return false;
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("\n🚀 ESP32-S3多传感器数据上传系统启动");
    Serial.println("=====================================");
    
    // 连接WiFi
    if (!connectWiFi()) {
        Serial.println("⚠️ WiFi连接失败，系统将继续尝试重连");
    }
    
    // 创建FreeRTOS任务
    xTaskCreate(waistSensorTask, "WaistSensor", 8192, NULL, 1, NULL);
    xTaskCreate(shoulderSensorTask, "ShoulderSensor", 8192, NULL, 1, NULL);
    xTaskCreate(wristSensorTask, "WristSensor", 8192, NULL, 1, NULL);
    xTaskCreate(collectionControlTask, "CollectionControl", 4096, NULL, 2, NULL);
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
    
    // 如果数据收集完成，等待一段时间后重启
    if (collection_completed) {
        Serial.println("🔄 数据收集完成，5秒后重启系统...");
        delay(5000);
        ESP.restart();
    }
    
    delay(5000);  // 5秒检查一次
} 