#include <WiFi.h>
#include <HTTPClient.h>
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
#define MAX_MEMORY_DATA 1000  // 内存中最多存储1000条数据

// 分块上传配置
#define MAX_BATCH_SIZE 100    // 每批最多100条数据
#define MAX_JSON_SIZE 8192    // JSON最大8KB

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

struct MemorySession {
    uint32_t session_id;
    uint32_t data_count;
    bool upload_complete;
    uint32_t uploaded_batches;
    uint32_t total_batches;
    SensorData data_buffer[MAX_MEMORY_DATA];
};

// 全局变量
QueueHandle_t dataQueue;
SemaphoreHandle_t memoryMutex;
MemorySession currentSession = {0};
bool wifiConnected = false;

// 任务句柄
TaskHandle_t dataCollectionTask;
TaskHandle_t dataUploadTask;
TaskHandle_t wifiTask;

void registerDeviceIP();
void markUploadComplete();
void uploadStoredData();
void storeDataToMemory(SensorData &data);
SensorData parseSensorData(uint8_t* buffer);
String createJSONBatch(uint32_t startIndex, uint32_t count);

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
                    
                    // 存储到内存
                    storeDataToMemory(data);
                    
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
        if (wifiConnected) {
            // 检查是否有数据需要上传
            uploadStoredData();
        }
        vTaskDelay(5000 / portTICK_PERIOD_MS); // 每5秒检查一次
    }
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

// ==================== 存储数据到内存 ====================
void storeDataToMemory(SensorData &data) {
    if (xSemaphoreTake(memoryMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        // 创建会话（如果不存在）
        if (currentSession.session_id == 0) {
            currentSession.session_id = millis();
            currentSession.data_count = 0;
            currentSession.upload_complete = false;
            currentSession.uploaded_batches = 0;
            currentSession.total_batches = 0;
            
            Serial.printf("📊 开始新会话: %u\n", currentSession.session_id);
        }
        
        // 检查内存是否已满
        if (currentSession.data_count < MAX_MEMORY_DATA) {
            // 存储数据到内存缓冲区
            currentSession.data_buffer[currentSession.data_count] = data;
            currentSession.data_count++;
            
            if (currentSession.data_count % 100 == 0) {
                Serial.printf("📊 已存储 %u 条数据到内存\n", currentSession.data_count);
            }
        } else {
            Serial.println("⚠️ 内存缓冲区已满，丢弃数据");
        }
        
        xSemaphoreGive(memoryMutex);
    }
}

// ==================== 创建JSON批次数据 ====================
String createJSONBatch(uint32_t startIndex, uint32_t count) {
    String jsonData = "[";
    
    for (uint32_t i = 0; i < count && (startIndex + i) < currentSession.data_count; i++) {
        SensorData &data = currentSession.data_buffer[startIndex + i];
        
        if (i > 0) jsonData += ",";
        
        jsonData += "{";
        jsonData += "\"acc\":[" + String(data.acc[0], 3) + "," + String(data.acc[1], 3) + "," + String(data.acc[2], 3) + "],";
        jsonData += "\"gyro\":[" + String(data.gyro[0], 3) + "," + String(data.gyro[1], 3) + "," + String(data.gyro[2], 3) + "],";
        jsonData += "\"angle\":[" + String(data.angle[0], 1) + "," + String(data.angle[1], 1) + "," + String(data.angle[2], 1) + "]";
        jsonData += "}";
    }
    
    jsonData += "]";
    return jsonData;
}

// ==================== 上传内存中的数据 ====================
void uploadStoredData() {
    if (currentSession.session_id == 0 || currentSession.upload_complete) {
        return;
    }
    
    if (currentSession.data_count == 0) {
        return;
    }
    
    // 计算总批次数（如果还没计算）
    if (currentSession.total_batches == 0) {
        currentSession.total_batches = (currentSession.data_count + MAX_BATCH_SIZE - 1) / MAX_BATCH_SIZE;
        Serial.printf("📊 总数据: %u, 总批次数: %u\n", currentSession.data_count, currentSession.total_batches);
    }
    
    // 检查是否还有批次需要上传
    if (currentSession.uploaded_batches >= currentSession.total_batches) {
        return;
    }
    
    // 计算当前批次的数据
    uint32_t startIndex = currentSession.uploaded_batches * MAX_BATCH_SIZE;
    uint32_t remainingData = currentSession.data_count - startIndex;
    uint32_t batchSize = min(MAX_BATCH_SIZE, remainingData);
    
    // 创建JSON数据
    String jsonData = createJSONBatch(startIndex, batchSize);
    
    // 发送HTTP请求
    HTTPClient http;
    http.begin(String(server_url) + "/wxapp/esp32/batch_upload/");
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    
    // 构建表单数据
    String postData = "device_code=" + String(device_code) + "&";
    postData += "session_id=" + String(currentSession.session_id) + "&";
    postData += "sensor_type=waist&"; // 默认传感器类型
    postData += "batch_data=" + jsonData;
    
    Serial.printf("📤 上传批次 %u/%u: %u 条数据\n", 
        currentSession.uploaded_batches + 1, currentSession.total_batches, batchSize);
    
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
            
            // 清空内存缓冲区
            currentSession.data_count = 0;
            currentSession.session_id = 0;
            
            Serial.println("🗑️ 已清空内存缓冲区");
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

// ==================== 设置函数 ====================
void setup() {
    Serial.begin(115200);
    Serial.println("🚀 ESP32 内存数据采集系统启动...");
    Serial.println("⚠️ 注意：使用内存存储，不依赖文件系统");
    
    // 创建队列和信号量
    dataQueue = xQueueCreate(QUEUE_SIZE, sizeof(SensorData));
    memoryMutex = xSemaphoreCreateMutex();
    
    if (dataQueue == NULL || memoryMutex == NULL) {
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
    Serial.printf("  - 内存缓冲区大小: %d 条数据\n", MAX_MEMORY_DATA);
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
        Serial.printf("  队列剩余: %d\n", uxQueueMessagesWaiting(dataQueue));
        Serial.printf("  当前会话: %u\n", currentSession.session_id);
        Serial.printf("  内存数据: %u/%u\n", currentSession.data_count, MAX_MEMORY_DATA);
        Serial.printf("  批次进度: %u/%u\n", currentSession.uploaded_batches, currentSession.total_batches);
        Serial.printf("  上传状态: %s\n", currentSession.upload_complete ? "已完成" : "未完成");
        Serial.println("-------------------");
        lastStatusTime = millis();
    }
} 