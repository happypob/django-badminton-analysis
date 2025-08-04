#include <SPIFFS.h>

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("🚀 ESP32 SPIFFS测试程序");
    
    // 测试SPIFFS初始化
    Serial.println("🔄 初始化SPIFFS...");
    
    if (!SPIFFS.begin(true)) { // true表示格式化
        Serial.println("❌ SPIFFS初始化失败!");
        return;
    }
    
    Serial.println("✅ SPIFFS初始化成功!");
    
    // 显示文件系统信息
    size_t totalBytes = SPIFFS.totalBytes();
    size_t usedBytes = SPIFFS.usedBytes();
    size_t freeBytes = totalBytes - usedBytes;
    
    Serial.printf("📊 Flash文件系统信息:\n");
    Serial.printf("  总空间: %d bytes (%.1f MB)\n", totalBytes, totalBytes / 1024.0 / 1024.0);
    Serial.printf("  已使用: %d bytes (%.1f MB)\n", usedBytes, usedBytes / 1024.0 / 1024.0);
    Serial.printf("  可用空间: %d bytes (%.1f MB)\n", freeBytes, freeBytes / 1024.0 / 1024.0);
    
    // 测试写入文件
    Serial.println("📝 测试写入文件...");
    File testFile = SPIFFS.open("/test.txt", "w");
    if (testFile) {
        testFile.println("Hello SPIFFS!");
        testFile.println("这是一个测试文件");
        testFile.printf("时间戳: %lu\n", millis());
        testFile.close();
        Serial.println("✅ 文件写入成功");
    } else {
        Serial.println("❌ 文件写入失败");
        return;
    }
    
    // 测试读取文件
    Serial.println("📖 测试读取文件...");
    File readFile = SPIFFS.open("/test.txt", "r");
    if (readFile) {
        Serial.println("📄 文件内容:");
        while (readFile.available()) {
            String line = readFile.readStringUntil('\n');
            Serial.println("  " + line);
        }
        readFile.close();
        Serial.println("✅ 文件读取成功");
    } else {
        Serial.println("❌ 文件读取失败");
    }
    
    // 列出所有文件
    Serial.println("📁 文件列表:");
    File root = SPIFFS.open("/");
    if (root) {
        File file = root.openNextFile();
        while (file) {
            if (!file.isDirectory()) {
                Serial.printf("  %s - %d bytes\n", file.name(), file.size());
            }
            file = root.openNextFile();
        }
        root.close();
    }
    
    Serial.println("🎉 SPIFFS测试完成!");
}

void loop() {
    delay(1000);
    Serial.printf("⏰ 运行时间: %lu 秒\n", millis() / 1000);
} 