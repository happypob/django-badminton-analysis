#include <WiFi.h>
#include <HTTPClient.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>
#include <esp_task_wdt.h>

#define UART1_RX 16
#define UART1_TX 17
#define UART1_BAUD 115200

// WiFi配置
const char* ssid = "xiaoming";
const char* password = "LZMSDSG0704";

// 服务器配置
const char* streaming_url = "http://47.122.129.159:8000/wxapp/esp32/upload/";
const char* device_code = "esp32s3_multi_001";
const int session_id = 1;  // 使用简单的会话ID

// 陀螺仪帧格式
#define FRAME_HEADER 0xAA
#define FRAME_TAIL   0x55
#define FRAME_SIZE   43  // 1+4+12+12+12+1+1

// 流式传输配置
#define STREAM_BUFFER_SIZE 5   // 减小缓冲区，提高实时性
#define MAX_SENSORS 4    // 支持最多4个陀螺仪
#define STREAM_INTERVAL 200  // 流式传输间隔(ms)

struct SensorData {
    uint8_t id;
    uint32_t timestamp_ms;
    float acc[3];
    float gyro[3];
    float angle[3];
};

// 优化的流式传输缓冲区 - 循环缓冲区
struct StreamBuffer {
    SensorData data[STREAM_BUFFER_SIZE];
    int head;           // 写入位置
    int tail;           // 读取位置
    int count;          // 当前数据量
    uint32_t lastUploadTime;
    bool isUploading;
    SemaphoreHandle_t mutex;  // 互斥锁
};

StreamBuffer streamBuffers[MAX_SENSORS];

// 数据统计
struct DataStats {
    uint32_t received_count[MAX_SENSORS];
    uint32_t streamed_count[MAX_SENSORS];
    uint32_t dropped_count[MAX_SENSORS];
    uint32_t last_receive_time[MAX_SENSORS];
    uint32_t last_stream_time[MAX_SENSORS];
    uint32_t buffer_overflow[MAX_SENSORS];
};

DataStats dataStats = {0};

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
        return true;
    } else {
        Serial.println("❌ WiFi连接失败!");
        return false;
    }
}

// 传感器类型映射函数
const char* getSensorType(uint8_t sensorId) {
    switch(sensorId) {
        case 1: return "waist";    // 腰部传感器
        case 2: return "shoulder"; // 肩部传感器
        case 3: return "wrist";    // 腕部传感器
        case 4: return "racket";   // 球拍传感器
        default: return "unknown";
    }
}

// 简单JSON构建
String buildJsonData(SensorData &data) {
    char jsonBuffer[256];
    snprintf(jsonBuffer, sizeof(jsonBuffer), 
        "{\"acc\":[%.2f,%.2f,%.2f],\"gyro\":[%.2f,%.2f,%.2f],\"angle\":[%.1f,%.1f,%.1f]}",
        data.acc[0], data.acc[1], data.acc[2],
        data.gyro[0], data.gyro[1], data.gyro[2],
        data.angle[0], data.angle[1], data.angle[2]
    );
    return String(jsonBuffer);
}

// 安全的缓冲区添加数据
bool addToStreamBuffer(uint8_t sensorId, SensorData &data) {
    if (sensorId < 1 || sensorId > MAX_SENSORS) return false;
    
    StreamBuffer &buffer = streamBuffers[sensorId - 1];
    
    if (xSemaphoreTake(buffer.mutex, pdMS_TO_TICKS(10)) == pdTRUE) {
        if (buffer.count < STREAM_BUFFER_SIZE) {
            // 缓冲区未满，添加数据
            buffer.data[buffer.head] = data;
            buffer.head = (buffer.head + 1) % STREAM_BUFFER_SIZE;
            buffer.count++;
        } else {
            // 缓冲区满，覆盖最旧的数据
            buffer.data[buffer.head] = data;
            buffer.head = (buffer.head + 1) % STREAM_BUFFER_SIZE;
            buffer.tail = (buffer.tail + 1) % STREAM_BUFFER_SIZE;
            dataStats.buffer_overflow[sensorId - 1]++;
        }
        xSemaphoreGive(buffer.mutex);
        return true;
    }
    return false;
}

// 安全的缓冲区获取数据
int getFromStreamBuffer(uint8_t sensorId, SensorData* dataArray, int maxCount) {
    if (sensorId < 1 || sensorId > MAX_SENSORS) return 0;
    
    StreamBuffer &buffer = streamBuffers[sensorId - 1];
    int count = 0;
    
    if (xSemaphoreTake(buffer.mutex, pdMS_TO_TICKS(10)) == pdTRUE) {
        count = min(buffer.count, maxCount);
        for (int i = 0; i < count; i++) {
            dataArray[i] = buffer.data[buffer.tail];
            buffer.tail = (buffer.tail + 1) % STREAM_BUFFER_SIZE;
        }
        buffer.count -= count;
        xSemaphoreGive(buffer.mutex);
    }
    return count;
}

// 流式传输单个传感器数据
bool streamSensorData(uint8_t sensorId) {
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }

    StreamBuffer &buffer = streamBuffers[sensorId - 1];
    if (buffer.count == 0) {
        return true; // 没有数据需要传输
    }

    const char* sensorType = getSensorType(sensorId);
    
    // 获取缓冲区中的所有数据
    SensorData dataArray[STREAM_BUFFER_SIZE];
    int dataCount = getFromStreamBuffer(sensorId, dataArray, STREAM_BUFFER_SIZE);
    
    if (dataCount == 0) return true;
    
    HTTPClient http;
    http.begin(streaming_url);
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");

    // 构建流式JSON数据 - 只发送最新的一条数据
    String postData = "device_code=" + String(device_code);
    postData += "&sensor_type=" + String(sensorType);
    postData += "&data=" + buildJsonData(dataArray[dataCount - 1]); // 发送最新数据
    postData += "&session_id=" + String(session_id);
    postData += "&timestamp=" + String(dataArray[dataCount - 1].timestamp_ms);
    postData += "&streaming=true"; // 标记为流式传输

    int httpResponseCode = http.POST(postData);

    bool success = false;
    if (httpResponseCode > 0) {
        String response = http.getString();
        if (httpResponseCode == 200) {
            dataStats.streamed_count[sensorId - 1]++;
            dataStats.last_stream_time[sensorId - 1] = millis();
            success = true;
        } else {
            Serial.printf("❌ %s传感器流式传输失败 (HTTP: %d)\n", sensorType, httpResponseCode);
        }
    } else {
        Serial.printf("❌ %s传感器流式传输网络错误: %s\n", sensorType, http.errorToString(httpResponseCode).c_str());
    }

    http.end();
    return success;
}

// 流式传输任务 - 实时处理传感器数据
void streamingTask(void* parameter) {
    Serial.println("📡 流式传输任务启动");
    
    uint32_t lastStreamTime = 0;
    uint32_t totalStreamCount = 0;

    while (true) {
        uint32_t now = millis();
        
        // 检查每个传感器的流式缓冲区
        for (int sensorId = 1; sensorId <= MAX_SENSORS; sensorId++) {
            StreamBuffer &buffer = streamBuffers[sensorId - 1];
            
            // 如果缓冲区有数据且超过传输间隔，则进行流式传输
            if (buffer.count > 0 && 
                !buffer.isUploading && 
                (now - buffer.lastUploadTime) >= STREAM_INTERVAL) {
                
                buffer.isUploading = true;
                if (streamSensorData(sensorId)) {
                    totalStreamCount++;
                }
                buffer.lastUploadTime = now;
                buffer.isUploading = false;
            }
        }
        
        // 每5秒打印一次流式传输统计
        static uint32_t lastPrintTime = 0;
        if (now - lastPrintTime >= 5000) {
            Serial.printf("📊 流式传输统计: 总计%lu条 | 传感器1:%lu 2:%lu 3:%lu 4:%lu\n", 
                totalStreamCount,
                dataStats.streamed_count[0],
                dataStats.streamed_count[1], 
                dataStats.streamed_count[2],
                dataStats.streamed_count[3]);
            lastPrintTime = now;
        }
        
        vTaskDelay(pdMS_TO_TICKS(10)); // 10ms检查间隔
    }
}

// 串口接收任务 - 专注于快速读取数据
void uartReceiveTask(void* parameter) {
    Serial.println("📥 UART接收任务启动 (流式模式)");
    uint8_t frame[FRAME_SIZE];
    size_t index = 0;
    uint32_t totalFrameCount = 0;
    uint32_t lastPrintTime = 0;
    uint32_t lastWatchdogReset = 0;

    while (true) {
        // 定期重置看门狗
        uint32_t now = millis();
        if (now - lastWatchdogReset >= 5000) {
            esp_task_wdt_reset();
            lastWatchdogReset = now;
        }
        
        while (Serial1.available()) {
            uint8_t byte = Serial1.read();

            // 寻找帧头
            if (index == 0 && byte != FRAME_HEADER) continue;

            frame[index++] = byte;

            // 检查完整帧
            if (index == FRAME_SIZE) {
                index = 0;
                if (frame[FRAME_SIZE - 1] != FRAME_TAIL) continue;

                // 解析数据
                SensorData data;
                memcpy(&data.timestamp_ms, &frame[1], 4);
                memcpy(data.acc, &frame[5], 12);
                memcpy(data.gyro, &frame[17], 12);
                memcpy(data.angle, &frame[29], 12);
                data.id = frame[41];

                // 验证传感器ID (1-4)
                if (data.id < 1 || data.id > MAX_SENSORS) {
                    Serial.printf("⚠️ 无效传感器ID: %d\n", data.id);
                    continue;
                }

                int sensorIdx = data.id - 1; // 转换为0-3的索引

                // 时间同步
                static uint32_t baseSystemTime[MAX_SENSORS] = {0};
                static uint32_t baseSensorTime[MAX_SENSORS] = {0};

                if (baseSystemTime[sensorIdx] == 0) {
                    baseSystemTime[sensorIdx] = millis();
                    baseSensorTime[sensorIdx] = data.timestamp_ms;
                }
                uint32_t nowSystem = millis();
                data.timestamp_ms = data.timestamp_ms - (baseSensorTime[sensorIdx]-baseSystemTime[sensorIdx]);

                // 更新统计信息
                dataStats.received_count[sensorIdx]++;
                dataStats.last_receive_time[sensorIdx] = millis();

                // 添加到流式缓冲区
                if (addToStreamBuffer(data.id, data)) {
                    totalFrameCount++;
                } else {
                    dataStats.dropped_count[sensorIdx]++;
                }

                // 每秒打印一次接收状态
                if (now - lastPrintTime >= 1000) {
                    Serial.printf("📊 接收状态: 总计%lu帧 | 传感器1:%lu 2:%lu 3:%lu 4:%lu\n", 
                        totalFrameCount,
                        dataStats.received_count[0],
                        dataStats.received_count[1], 
                        dataStats.received_count[2],
                        dataStats.received_count[3]);
                    lastPrintTime = now;
                }
            }
        }
        vTaskDelay(pdMS_TO_TICKS(1));  // 最小延迟，保证读取速度
    }
}

void setup() {
    Serial.begin(115200);
    Serial1.begin(UART1_BAUD, SERIAL_8N1, UART1_RX, UART1_TX);

    Serial.println("🚀 ESP32 羽毛球传感器流式传输系统启动 (优化版)");
    Serial.println("========================================");
    Serial.printf("流式缓冲区大小: %d (循环缓冲区)\n", STREAM_BUFFER_SIZE);
    Serial.printf("流式传输间隔: %d ms\n", STREAM_INTERVAL);
    Serial.printf("支持传感器数量: %d\n", MAX_SENSORS);
    Serial.printf("传感器类型: 1=腰部 2=肩部 3=腕部 4=球拍\n");
    Serial.printf("数据频率: 10ms/帧 (100Hz)\n");
    Serial.printf("流式传输接口: %s\n", streaming_url);
    Serial.println("========================================");

    // 初始化流式缓冲区
    for (int i = 0; i < MAX_SENSORS; i++) {
        streamBuffers[i].head = 0;
        streamBuffers[i].tail = 0;
        streamBuffers[i].count = 0;
        streamBuffers[i].lastUploadTime = 0;
        streamBuffers[i].isUploading = false;
        streamBuffers[i].mutex = xSemaphoreCreateMutex();
    }

    // 配置看门狗
    esp_task_wdt_config_t wdt_config = {
        .timeout_ms = 30000,
        .idle_core_mask = (1 << 0) | (1 << 1),
        .trigger_panic = true
    };
    esp_task_wdt_init(&wdt_config);
    esp_task_wdt_add(NULL);
    Serial.println("✅ 看门狗已配置 (30秒超时)");

    // 连接WiFi
    connectWiFi();

    // 启动接收任务 - 高优先级，专注于数据读取
    xTaskCreatePinnedToCore(uartReceiveTask, "UartReceiveTask", 16384, NULL, 3, NULL, 0);
    Serial.println("✅ UART接收任务已启动 (核心0, 优先级3, 栈16KB)");

    // 启动流式传输任务 - 中等优先级，处理实时传输
    xTaskCreatePinnedToCore(streamingTask, "StreamingTask", 16384, NULL, 2, NULL, 1);
    Serial.println("✅ 流式传输任务已启动 (核心1, 优先级2, 栈16KB)");
}

void loop() {
    // 主循环处理WiFi重连和状态监控
    static uint32_t lastStatusTime = 0;
    uint32_t now = millis();
    
    // 重置看门狗
    esp_task_wdt_reset();
    
    // 检查WiFi连接
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("⚠️ WiFi连接断开，尝试重连...");
        connectWiFi();
    }
    
    // 每10秒打印一次详细系统状态
    if (now - lastStatusTime >= 10000) {
        Serial.println("=== 流式传输系统状态 ===");
        Serial.printf("WiFi状态: %s\n", WiFi.status() == WL_CONNECTED ? "已连接" : "未连接");
        
        // 内存信息
        Serial.printf("可用堆内存: %lu bytes\n", ESP.getFreeHeap());
        Serial.printf("最小可用堆内存: %lu bytes\n", ESP.getMinFreeHeap());
        
        // 各传感器统计
        Serial.println("--- 传感器流式传输统计 ---");
        const char* sensorNames[] = {"腰部", "肩部", "腕部", "球拍"};
        for (int i = 0; i < MAX_SENSORS; i++) {
            uint32_t sensorId = i + 1;
            uint32_t received = dataStats.received_count[i];
            uint32_t streamed = dataStats.streamed_count[i];
            uint32_t dropped = dataStats.dropped_count[i];
            uint32_t overflow = dataStats.buffer_overflow[i];
            uint32_t lastReceiveTime = dataStats.last_receive_time[i];
            uint32_t lastStreamTime = dataStats.last_stream_time[i];
            int bufferCount = streamBuffers[i].count;
            
            // 计算流式传输延迟
            uint32_t streamDelay = (lastReceiveTime > 0 && lastStreamTime > 0) ? 
                (lastStreamTime - lastReceiveTime) : 0;
            
            Serial.printf("%s传感器(ID%d): 接收%lu 流式传输%lu 丢弃%lu 溢出%lu 缓冲区%d 延迟%lu\n", 
                sensorNames[i], sensorId, received, streamed, dropped, overflow, bufferCount, streamDelay);
        }
        
        Serial.printf("运行时间: %lu ms\n", now);
        Serial.println("================");
        lastStatusTime = now;
    }
    
    delay(1000);
} 