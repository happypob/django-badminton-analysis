#include <WiFi.h>
#include <HTTPClient.h>
#include <LittleFS.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>
#include <freertos/semphr.h>

// 硬件配置
#define UART1_RX 16
#define UART1_TX 17
#define UART1_BAUD 115200

// WiFi配置
const char* ssid = "xiaoming";
const char* password = "LZMSDSG0704";

// 服务器配置
const char* server_url = "http://47.122.129.159:8000";
const char* device_code = "2025001";

// Arduino FreeRTOS任务配置
#define TASK_STACK_SIZE 4096
#define QUEUE_SIZE 100
#define BATCH_SIZE 50

// 分块上传配置
#define MAX_BATCH_SIZE 100    // 每批最多100条数据
#define MAX_JSON_SIZE 8192    // JSON最大8KB
#define MAX_LINE_LENGTH 256   // 单行最大256字符

// 陀螺仪帧格式
#define FRAME_HEADER 0xAA
#define FRAME_TAIL   0x55
#define FRAME_SIZE   43

// 数据结构
struct SensorData {
    uint8_t id;
    uint32_t timestamp_ms;
    float acc[3];
    float gyro[3];
    float angle[3];
};

struct UploadSession {
    uint32_t session_id;
    uint32_t data_count;
    uint32_t file_size;
    String filename;
    bool upload_complete;
    uint32_t uploaded_batches;
    uint32_t total_batches;
    uint32_t current_line_position;
};

// 全局变量
QueueHandle_t dataQueue;
SemaphoreHandle_t fsMutex;
UploadSession currentSession = {0};
bool fsReady = false;
bool wifiConnected = false;

// 任务句柄
TaskHandle_t dataCollectionTask;
TaskHandle_t dataUploadTask;
TaskHandle_t wifiTask;

void registerDeviceIP();
void markUploadComplete();
void uploadStoredData();
void storeDataToFS(SensorData &data);
SensorData parseSensorData(uint8_t* buffer);
void debugFS();


// ==================== WiFi连接任务 ====================
void wifiTaskFunction(void* parameter) {
    while (true) {
        if (WiFi.status() != WL_CONNECTED) {
            Serial.println("🔄 连接WiFi...");
            WiFi.mode(WIFI_STA);
            WiFi.begin(ssid, password);
            
            int attempts = 0;
            while (WiFi.status() != WL_CONNECTED && attempts < 20) {
                attempts++;
                Serial.printf("尝试连接 %d/20\n", attempts);
                vTaskDelay(1000 / portTICK_PERIOD_MS);
            }
            
            if (WiFi.status() == WL_CONNECTED) {
                Serial.println("✅ WiFi连接成功!");
                Serial.printf("IP: %s\n", WiFi.localIP().toString().c_str());
                wifiConnected = true;
                
                // 注册设备IP
                registerDeviceIP();
            } else {
                Serial.println("❌ WiFi连接失败!");
                wifiConnected = false;
            }
        }
        vTaskDelay(10000 / portTICK_PERIOD_MS); // 每10秒检查一次
    }
}

// ==================== 数据采集任务 ====================
void dataCollectionTaskFunction(void* parameter) {
    uint8_t rxBuffer[256];
    int bufferIndex = 0;
    
    Serial1.begin(UART1_BAUD, SERIAL_8N1, UART1_RX, UART1_TX);
    
    while (true) {
        if (Serial1.available()) {
            uint8_t byte = Serial1.read();
            rxBuffer[bufferIndex++] = byte;
            
            // 检查帧头
            if (bufferIndex == 1 && byte != FRAME_HEADER) {
                bufferIndex = 0;
                continue;
            }
            
            // 检查帧尾
            if (bufferIndex > 1 && byte == FRAME_TAIL) {
                if (bufferIndex == FRAME_SIZE) {
                    // 解析传感器数据
                    SensorData data = parseSensorData(rxBuffer);
                    
                    // 存储到Flash文件系统
                    if (fsReady) {
                        storeDataToFS(data);
                    }
                    
                    // 发送到上传队列
                    if (xQueueSend(dataQueue, &data, 0) != pdTRUE) {
                        Serial.println("⚠️ 队列已满，丢弃数据");
                    }
                }
                bufferIndex = 0;
            }
            
            // 防止缓冲区溢出
            if (bufferIndex >= sizeof(rxBuffer)) {
                bufferIndex = 0;
            }
        }
        vTaskDelay(1 / portTICK_PERIOD_MS);
    }
}

// ==================== 数据上传任务 ====================
void dataUploadTaskFunction(void* parameter) {
    while (true) {
        if (wifiConnected && fsReady) {
            // 检查是否有完整的数据文件需要上传
            uploadStoredData();
        }
        vTaskDelay(5000 / portTICK_PERIOD_MS); // 每5秒检查一次
    }
}

// ==================== LittleFS初始化 ====================
bool initLittleFS() {
    Serial.println("🔄 初始化LittleFS文件系统...");
    
    // 首先尝试挂载
    if (!LittleFS.begin(false)) { // false表示不格式化
        Serial.println("⚠️ 挂载失败，尝试格式化...");
        
        // 尝试格式化
        if (!LittleFS.format()) {
            Serial.println("❌ 格式化失败!");
            return false;
        }
        
        Serial.println("✅ 格式化完成，重新挂载...");
        
        // 重新挂载
        if (!LittleFS.begin(false)) {
            Serial.println("❌ 重新挂载失败!");
            return false;
        }
    }
    
    Serial.println("✅ LittleFS初始化成功!");
    
    // 显示文件系统信息
    size_t totalBytes = LittleFS.totalBytes();
    size_t usedBytes = LittleFS.usedBytes();
    size_t freeBytes = totalBytes - usedBytes;
    
    Serial.printf("📊 Flash文件系统信息:\n");
    Serial.printf("  总空间: %d bytes (%.1f MB)\n", totalBytes, totalBytes / 1024.0 / 1024.0);
    Serial.printf("  已使用: %d bytes (%.1f MB)\n", usedBytes, usedBytes / 1024.0 / 1024.0);
    Serial.printf("  可用空间: %d bytes (%.1f MB)\n", freeBytes, freeBytes / 1024.0 / 1024.0);
    
    // 列出现有文件
    Serial.println("📁 现有文件:");
    File root = LittleFS.open("/");
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
    
    return true;
}

// ==================== 解析传感器数据 ====================
SensorData parseSensorData(uint8_t* buffer) {
    SensorData data = {0};
    
    data.id = buffer[1];
    data.timestamp_ms = millis();
    
    // 解析加速度数据 (4字节浮点数)
    memcpy(&data.acc[0], &buffer[2], 4);
    memcpy(&data.acc[1], &buffer[6], 4);
    memcpy(&data.acc[2], &buffer[10], 4);
    
    // 解析陀螺仪数据
    memcpy(&data.gyro[0], &buffer[14], 4);
    memcpy(&data.gyro[1], &buffer[18], 4);
    memcpy(&data.gyro[2], &buffer[22], 4);
    
    // 解析角度数据
    memcpy(&data.angle[0], &buffer[26], 4);
    memcpy(&data.angle[1], &buffer[30], 4);
    memcpy(&data.angle[2], &buffer[34], 4);
    
    return data;
}

// ==================== 存储数据到Flash文件系统 ====================
void storeDataToFS(SensorData &data) {
    if (xSemaphoreTake(fsMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        // 创建会话文件（如果不存在）
        if (currentSession.session_id == 0) {
            currentSession.session_id = millis();
            currentSession.filename = "/session_" + String(currentSession.session_id) + ".dat";
            currentSession.data_count = 0;
            currentSession.file_size = 0;
            currentSession.upload_complete = false;
            currentSession.uploaded_batches = 0;
            currentSession.total_batches = 0;
            currentSession.current_line_position = 0;
            
            // 创建会话信息文件
            File infoFile = LittleFS.open("/session_" + String(currentSession.session_id) + ".info", "w");
            if (infoFile) {
                infoFile.println("Session ID: " + String(currentSession.session_id));
                infoFile.println("Start Time: " + String(millis()));
                infoFile.println("Device: " + String(device_code));
                infoFile.close();
            }
        }
        
        // 写入数据文件
        File dataFile = LittleFS.open(currentSession.filename, "a");
        if (dataFile) {
            // 写入数据记录
            dataFile.printf("%u,%u,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.1f,%.1f,%.1f\n",
                data.id, data.timestamp_ms,
                data.acc[0], data.acc[1], data.acc[2],
                data.gyro[0], data.gyro[1], data.gyro[2],
                data.angle[0], data.angle[1], data.angle[2]
            );
            dataFile.close();
            
            currentSession.data_count++;
            currentSession.file_size = LittleFS.open(currentSession.filename, "r").size();
            
            if (currentSession.data_count % 100 == 0) {
                Serial.printf("📊 已存储 %u 条数据，文件大小: %u bytes\n", 
                    currentSession.data_count, currentSession.file_size);
            }
        }
        xSemaphoreGive(fsMutex);
    }
}

// ==================== 读取数据批次并转换为JSON ====================
String readDataBatchAsJSON() {
    File dataFile = LittleFS.open(currentSession.filename, "r");
    if (!dataFile) {
        Serial.printf("❌ 无法打开数据文件: %s\n", currentSession.filename.c_str());
        return "";
    }
    
    // 定位到当前读取位置
    dataFile.seek(currentSession.current_line_position);
    
    String jsonData = "[";
    
    bool firstRecord = true;
    int batchCount = 0;
    
    while (dataFile.available() && batchCount < MAX_BATCH_SIZE) {
        String line = dataFile.readStringUntil('\n');
        if (line.length() > 0 && line.length() < MAX_LINE_LENGTH) {
            // 解析CSV行
            int commaIndex = 0;
            String parts[11];
            int partIndex = 0;
            
            for (int i = 0; i < line.length() && partIndex < 11; i++) {
                if (line.charAt(i) == ',') {
                    parts[partIndex++] = line.substring(commaIndex, i);
                    commaIndex = i + 1;
                }
            }
            if (partIndex < 11) {
                parts[partIndex] = line.substring(commaIndex);
            }
            
            // 检查JSON大小限制
            String recordJson = "{";
            recordJson += "\"acc\":[" + parts[2] + "," + parts[3] + "," + parts[4] + "],";
            recordJson += "\"gyro\":[" + parts[5] + "," + parts[6] + "," + parts[7] + "],";
            recordJson += "\"angle\":[" + parts[8] + "," + parts[9] + "," + parts[10] + "]";
            recordJson += "}";
            
            // 检查是否会超出JSON大小限制
            if ((jsonData.length() + recordJson.length() + 10) > MAX_JSON_SIZE) {
                break;
            }
            
            if (!firstRecord) jsonData += ",";
            jsonData += recordJson;
            firstRecord = false;
            batchCount++;
        }
    }
    
    // 更新文件位置
    currentSession.current_line_position = dataFile.position();
    dataFile.close();
    
    jsonData += "]";
    
    Serial.printf("📦 批次 %u: 读取了 %d 条数据，JSON大小: %d bytes\n", 
        currentSession.uploaded_batches + 1, batchCount, jsonData.length());
    
    return jsonData;
}

// ==================== 分块上传数据 ====================
void uploadStoredData() {
    // 检查是否有有效的会话和文件
    if (currentSession.session_id == 0) {
        return; // 没有会话，不需要上传
    }
    
    // 检查文件是否存在
    if (!LittleFS.exists(currentSession.filename)) {
        Serial.printf("⚠️ 文件不存在: %s\n", currentSession.filename.c_str());
        return;
    }
    
    if (currentSession.upload_complete) {
        return;
    }
    
    // 计算总批次数（如果还没计算）
    if (currentSession.total_batches == 0) {
        File dataFile = LittleFS.open(currentSession.filename, "r");
        if (!dataFile) {
            Serial.printf("❌ 无法打开数据文件: %s\n", currentSession.filename.c_str());
            return;
        }
        
        int lineCount = 0;
        while (dataFile.available()) {
            String line = dataFile.readStringUntil('\n');
            if (line.length() > 0) lineCount++;
        }
        dataFile.close();
        
        currentSession.total_batches = (lineCount + MAX_BATCH_SIZE - 1) / MAX_BATCH_SIZE;
        Serial.printf("📊 文件总行数: %d, 总批次数: %u\n", lineCount, currentSession.total_batches);
    }
    
    // 读取并上传当前批次
    String jsonData = readDataBatchAsJSON();
    if (jsonData.length() == 0) {
        Serial.println("❌ 无法读取数据批次");
        return;
    }
    
    // 发送HTTP请求
    HTTPClient http;
    http.begin(String(server_url) + "/wxapp/esp32/batch_upload/");
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    
    // 构建表单数据
    String postData = "device_code=" + String(device_code) + "&";
    postData += "session_id=" + String(currentSession.session_id) + "&";
    postData += "sensor_type=waist&"; // 默认传感器类型
    postData += "batch_data=" + jsonData;
    
    Serial.printf("📤 上传数据: %s\n", postData.substring(0, 200).c_str()); // 只显示前200字符
    
    int httpResponseCode = http.POST(postData);
    
    if (httpResponseCode == 200) {
        Serial.printf("✅ 批次 %u/%u 上传成功!\n", 
            currentSession.uploaded_batches + 1, currentSession.total_batches);
        currentSession.uploaded_batches++;
        
        // 检查是否所有批次都上传完成
        if (currentSession.uploaded_batches >= currentSession.total_batches) {
            Serial.println("🎉 所有批次上传完成!");
            currentSession.upload_complete = true;
            
            // 标记上传完成
            markUploadComplete();
            
            // 删除已上传的文件
            LittleFS.remove(currentSession.filename);
            LittleFS.remove("/session_" + String(currentSession.session_id) + ".info");
            
            Serial.println("🗑️ 已删除上传文件");
        }
    } else {
        Serial.printf("❌ 批次上传失败，HTTP代码: %d\n", httpResponseCode);
        Serial.println(http.getString());
    }
    
    http.end();
}

// ==================== 注册设备IP ====================
void registerDeviceIP() {
    HTTPClient http;
    
    http.begin(String(server_url) + "/wxapp/register_device_ip/");
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    
    String postData = "device_code=" + String(device_code) + "&ip_address=" + WiFi.localIP().toString();
    
    Serial.printf("📤 注册设备IP: %s\n", postData.c_str());
    
    int httpResponseCode = http.POST(postData);
    
    if (httpResponseCode == 200) {
        Serial.println("✅ 设备IP注册成功!");
    } else {
        Serial.printf("❌ IP注册失败，HTTP代码: %d\n", httpResponseCode);
        String response = http.getString();
        Serial.printf("响应内容: %s\n", response.c_str());
    }
    
    http.end();
}

// ==================== 标记上传完成 ====================
void markUploadComplete() {
    HTTPClient http;
    http.begin(String(server_url)+ "/wxapp/esp32/mark_upload_complete/");
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    
    String postData = "device_code=" + String(device_code) + "&";
    postData += "session_id=" + String(currentSession.session_id);
    
    int httpResponseCode = http.POST(postData);
    
    if (httpResponseCode == 200) {
        Serial.println("✅ 上传完成标记成功!");
    } else {
        Serial.printf("❌ 标记失败，HTTP代码: %d\n", httpResponseCode);
    }
    
    http.end();
}

// ==================== 调试Flash文件系统状态 ====================
void debugFS() {
    Serial.println("🔍 调试Flash文件系统状态:");
    
    // 列出根目录文件
    File root = LittleFS.open("/");
    if (!root) {
        Serial.println("❌ 无法打开根目录");
        return;
    }
    
    Serial.println("📁 根目录文件列表:");
    File file = root.openNextFile();
    while (file) {
        if (!file.isDirectory()) {
            Serial.printf("  %s - %d bytes\n", file.name(), file.size());
        }
        file = root.openNextFile();
    }
    root.close();
    
    // 检查当前会话文件
    if (currentSession.session_id != 0) {
        Serial.printf("📄 当前会话文件: %s\n", currentSession.filename.c_str());
        if (LittleFS.exists(currentSession.filename)) {
            File testFile = LittleFS.open(currentSession.filename, "r");
            if (testFile) {
                Serial.printf("✅ 文件存在，大小: %d bytes\n", testFile.size());
                testFile.close();
            } else {
                Serial.println("❌ 文件存在但无法打开");
            }
        } else {
            Serial.println("❌ 文件不存在");
        }
    }
}

// ==================== 设置函数 ====================
void setup() {
    Serial.begin(115200);
    Serial.println("🚀 ESP32 Flash数据采集系统启动...");
    
    // 初始化LittleFS
    fsReady = initLittleFS();
    
    // 如果初始化失败，尝试强制格式化
    if (!fsReady) {
        Serial.println("🔄 尝试强制格式化LittleFS...");
        if (LittleFS.format()) {
            Serial.println("✅ 强制格式化成功，重新初始化...");
            fsReady = initLittleFS();
        } else {
            Serial.println("❌ 强制格式化也失败了!");
        }
    }
    
    // 创建队列和信号量
    dataQueue = xQueueCreate(QUEUE_SIZE, sizeof(SensorData));
    fsMutex = xSemaphoreCreateMutex();
    
    if (dataQueue == NULL || fsMutex == NULL) {
        Serial.println("❌ 创建队列或信号量失败!");
        return;
    }
    
    // 创建Arduino FreeRTOS任务
    xTaskCreatePinnedToCore(
        wifiTaskFunction,      // 任务函数
        "WiFiTask",           // 任务名称
        TASK_STACK_SIZE,      // 堆栈大小
        NULL,                 // 参数
        1,                    // 优先级
        &wifiTask,            // 任务句柄
        0                     // 核心ID
    );
    
    xTaskCreatePinnedToCore(
        dataCollectionTaskFunction,
        "DataCollectionTask",
        TASK_STACK_SIZE,
        NULL,
        2,
        &dataCollectionTask,
        1
    );
    
    xTaskCreatePinnedToCore(
        dataUploadTaskFunction,
        "DataUploadTask",
        TASK_STACK_SIZE,
        NULL,
        1,
        &dataUploadTask,
        0
    );
    
    Serial.println("✅ 系统初始化完成!");
    Serial.println("📊 任务已启动:");
    Serial.println("  - WiFi连接任务");
    Serial.println("  - 数据采集任务");
    Serial.println("  - 数据上传任务");
}

// ==================== 主循环 ====================
void loop() {
    // 主循环保持空闲，所有工作由FreeRTOS任务处理
    vTaskDelay(1000 / portTICK_PERIOD_MS);
    
    // 打印系统状态
    static uint32_t lastStatusTime = 0;
    if (millis() - lastStatusTime > 30000) { // 每30秒打印一次状态
        Serial.println("📊 系统状态:");
        Serial.printf("  WiFi: %s\n", wifiConnected ? "已连接" : "未连接");
        Serial.printf("  Flash: %s\n", fsReady ? "就绪" : "未就绪");
        Serial.printf("  队列剩余: %d\n", uxQueueMessagesWaiting(dataQueue));
        Serial.printf("  当前会话: %u\n", currentSession.session_id);
        Serial.printf("  数据计数: %u\n", currentSession.data_count);
        Serial.printf("  文件大小: %u bytes\n", currentSession.file_size);
        Serial.printf("  批次进度: %u/%u\n", currentSession.uploaded_batches, currentSession.total_batches);
        Serial.printf("  上传状态: %s\n", currentSession.upload_complete ? "已完成" : "未完成");
        Serial.println("-------------------");
        
        // 每5分钟调试一次Flash文件系统状态
        static uint32_t lastDebugTime = 0;
        if (millis() - lastDebugTime > 300000) { // 5分钟
            debugFS();
            lastDebugTime = millis();
        }
        
        lastStatusTime = millis();
    }
} 