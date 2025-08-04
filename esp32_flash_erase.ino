#include <WiFi.h>
#include <HTTPClient.h>

// WiFi配置
const char* ssid = "xiaoming";
const char* password = "LZMSDSG0704";

// 服务器配置
const char* server_url = "http://47.122.129.159:8000";
const char* device_code = "2025001";

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("🚀 ESP32 基本功能测试程序");
    Serial.println("⚠️ 注意：Flash文件系统已损坏，使用内存存储");
    
    // 测试WiFi连接
    Serial.println("🔄 连接WiFi...");
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        attempts++;
        Serial.printf("尝试连接 %d/20\n", attempts);
        delay(1000);
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("✅ WiFi连接成功!");
        Serial.printf("IP: %s\n", WiFi.localIP().toString().c_str());
        
        // 测试HTTP连接
        testHTTPConnection();
    } else {
        Serial.println("❌ WiFi连接失败!");
    }
}

void testHTTPConnection() {
    HTTPClient http;
    
    // 测试注册设备IP
    Serial.println("📤 测试注册设备IP...");
    http.begin(String(server_url) + "/wxapp/register_device_ip/");
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    
    String postData = "device_code=" + String(device_code) + "&ip_address=" + WiFi.localIP().toString();
    
    int httpResponseCode = http.POST(postData);
    
    if (httpResponseCode == 200) {
        Serial.println("✅ 设备IP注册成功!");
        String response = http.getString();
        Serial.println("响应: " + response);
    } else {
        Serial.printf("❌ IP注册失败，HTTP代码: %d\n", httpResponseCode);
        String response = http.getString();
        Serial.println("响应: " + response);
    }
    
    http.end();
}

void loop() {
    delay(5000);
    Serial.printf("⏰ 运行时间: %lu 秒, WiFi状态: %s\n", 
        millis() / 1000, 
        WiFi.status() == WL_CONNECTED ? "已连接" : "未连接");
} 