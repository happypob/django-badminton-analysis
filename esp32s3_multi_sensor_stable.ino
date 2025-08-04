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
const char* device_code = "2025001";  // 测试设备码
const int session_id = 123;

// FreeRTOS队列
QueueHandle_t dataQueue;

// 简化的数据结构
struct SensorData {
    char sensor_type[10];  // 固定长度字符串
    float acc[3];
    float gyro[3];
    float angle[3];
    unsigned long timestamp;
};

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

// 简化的数据上传函数
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

// 腰部传感器任务 - 简化版本
void waistSensorTask(void* parameter) {
    Serial.println(" 腰部传感器任务启动");
    
    while (true) {
        // 模拟数据
        float acc[3] = {1.2 + random(-5, 5) * 0.1, 0.8 + random(-5, 5) * 0.1, 9.8 + random(-5, 5) * 0.1};
        float gyro[3] = {0.1 + random(-5, 5) * 0.01, 0.2 + random(-5, 5) * 0.01, 0.3 + random(-5, 5) * 0.01};
        float angle[3] = {45.0 + random(-5, 5), 30.0 + random(-5, 5), 60.0 + random(-5, 5)};
        
        // 直接上传，不使用队列
        uploadSensorData("waist", acc, gyro, angle);
        
        vTaskDelay(pdMS_TO_TICKS(2000));  // 2秒间隔
    }
}

// 肩部传感器任务 - 简化版本
void shoulderSensorTask(void* parameter) {
    Serial.println(" 肩部传感器任务启动");
    
    while (true) {
        // 模拟数据
        float acc[3] = {1.5 + random(-5, 5) * 0.1, 1.0 + random(-5, 5) * 0.1, 9.8 + random(-5, 5) * 0.1};
        float gyro[3] = {0.2 + random(-5, 5) * 0.01, 0.3 + random(-5, 5) * 0.01, 0.4 + random(-5, 5) * 0.01};
        float angle[3] = {50.0 + random(-5, 5), 35.0 + random(-5, 5), 65.0 + random(-5, 5)};
        
        // 直接上传，不使用队列
        uploadSensorData("shoulder", acc, gyro, angle);
        
        vTaskDelay(pdMS_TO_TICKS(2500));  // 2.5秒间隔
    }
}

// 腕部传感器任务 - 简化版本
void wristSensorTask(void* parameter) {
    Serial.println(" 腕部传感器任务启动");
    
    while (true) {
        // 模拟数据
        float acc[3] = {2.0 + random(-5, 5) * 0.1, 1.5 + random(-5, 5) * 0.1, 9.8 + random(-5, 5) * 0.1};
        float gyro[3] = {0.3 + random(-5, 5) * 0.01, 0.4 + random(-5, 5) * 0.01, 0.5 + random(-5, 5) * 0.01};
        float angle[3] = {55.0 + random(-5, 5), 40.0 + random(-5, 5), 70.0 + random(-5, 5)};
        
        // 直接上传，不使用队列
        uploadSensorData("wrist", acc, gyro, angle);
        
        vTaskDelay(pdMS_TO_TICKS(3000));  // 3秒间隔
    }
}

// 状态监控任务 - 简化版本
void statusMonitorTask(void* parameter) {
    Serial.println("📊 状态监控任务启动");
    
    while (true) {
        Serial.println("=== 系统状态 ===");
        Serial.printf("WiFi状态: %s\n", WiFi.status() == WL_CONNECTED ? "已连接" : "未连接");
        Serial.printf("WiFi信号强度: %d dBm\n", WiFi.RSSI());
        Serial.printf("可用堆内存: %d bytes\n", ESP.getFreeHeap());
        Serial.printf("任务运行时间: %lu ms\n", millis());
        Serial.println("================");
        
        vTaskDelay(pdMS_TO_TICKS(15000));  // 15秒间隔
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
    
    // 创建FreeRTOS任务 - 增加栈大小
    xTaskCreate(waistSensorTask, "WaistSensor", 8192, NULL, 1, NULL);
    xTaskCreate(shoulderSensorTask, "ShoulderSensor", 8192, NULL, 1, NULL);
    xTaskCreate(wristSensorTask, "WristSensor", 8192, NULL, 1, NULL);
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
    
    delay(10000);  // 10秒检查一次
} 