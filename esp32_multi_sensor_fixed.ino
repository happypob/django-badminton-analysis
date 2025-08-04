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

// 服务器配置 - 修复：使用正确的批量上传接口
const char* server_url = "http://47.122.129.159:8000/wxapp/esp32/batch_upload/";
const char* device_code = "esp32s3_multi_001";
const int session_id = 1011;

// 陀螺仪帧格式
#define FRAME_HEADER 0xAA
#define FRAME_TAIL   0x55
#define FRAME_SIZE   43  // 1+4+12+12+12+1+1

// 队列配置 - 优化为高频数据采集
#define QUEUE_SIZE 500   // 平衡内存使用和数据缓冲
#define BATCH_SIZE 50    // 平衡上传效率和内存使用
#define MAX_SENSORS 4    // 支持最多4个陀螺仪

struct SensorData {
    uint8_t id;
    uint32_t timestamp_ms; // 系统同步时间
    float acc[3];
    float gyro[3];
    float angle[3];
};

// 队列句柄
QueueHandle_t dataQueue;

// 数据统计
struct DataStats {
    uint32_t received_count[MAX_SENSORS];
    uint32_t uploaded_count[MAX_SENSORS];
    uint32_t dropped_count[MAX_SENSORS];
    uint32_t last_receive_time[MAX_SENSORS];
};

DataStats dataStats = {0};

// 串口缓冲
uint8_t rxBuffer[256];  // 增大缓冲区

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

// 批量上传传感器数据 - 修复：使用正确的接口和参数格式
bool uploadBatchSensorData(SensorData* dataArray, int count) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("⚠️ WiFi未连接，跳过批量上传");
        return false;
    }

    // 按传感器ID分组 - 使用动态分配避免栈溢出
    int groupCount[MAX_SENSORS] = {0};
    
    // 第一遍：统计每个传感器的数据量
    for (int i = 0; i < count; i++) {
        int sensorId = dataArray[i].id - 1; // 转换为0-3的索引
        if (sensorId >= 0 && sensorId < MAX_SENSORS) {
            groupCount[sensorId]++;
        }
    }
    
    bool allSuccess = true;
    
    // 为每个传感器组分别上传
    for (int sensorId = 0; sensorId < MAX_SENSORS; sensorId++) {
        if (groupCount[sensorId] > 0) {
            // 使用正确的传感器类型映射
            const char* sensorType = getSensorType(sensorId + 1);
            
            HTTPClient http;
            http.begin(server_url);  // 修复：使用正确的批量上传接口
            http.addHeader("Content-Type", "application/x-www-form-urlencoded");

            // 构建该传感器的批量JSON数据 - 修复：使用正确的参数格式
            String postData = "device_code=" + String(device_code);
            postData += "&sensor_type=" + String(sensorType);  // 修复：使用正确的传感器类型
            postData += "&batch_data=[";  // 修复：使用batch_data参数名
            
            int dataCount = 0;
            for (int i = 0; i < count && dataCount < groupCount[sensorId]; i++) {
                if (dataArray[i].id == sensorId + 1) {
                    if (dataCount > 0) postData += ",";
                    postData += buildJsonData(dataArray[i]);
                    dataCount++;
                }
            }
            postData += "]";
            postData += "&session_id=" + String(session_id);

            Serial.printf("📤 上传%s传感器: %d条数据\n", sensorType, groupCount[sensorId]);

            int httpResponseCode = http.POST(postData);

            if (httpResponseCode > 0) {
                String response = http.getString();
                Serial.printf("✅ %s传感器上传成功 (HTTP: %d)\n", sensorType, httpResponseCode);
                dataStats.uploaded_count[sensorId] += groupCount[sensorId];
            } else {
                Serial.printf("❌ %s传感器上传失败 (HTTP错误: %d)\n", sensorType, httpResponseCode);
                Serial.printf("错误详情: %s\n", http.errorToString(httpResponseCode).c_str());
                allSuccess = false;
            }

            http.end();
            
            // 给其他任务一些CPU时间
            vTaskDelay(pdMS_TO_TICKS(1));
        }
    }
    
    return allSuccess;
}

// 单个数据上传（备用）- 修复：使用单个数据上传接口
bool uploadSensorData(SensorData &data) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("⚠️ WiFi未连接，跳过上传");
        return false;
    }

    HTTPClient http;
    // 修复：使用单个数据上传接口
    http.begin("http://47.122.129.159:8000/wxapp/esp32/upload/");
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");

    String jsonData = buildJsonData(data);
    const char* sensorType = getSensorType(data.id);  // 修复：使用正确的传感器类型

    String postData = "device_code=" + String(device_code);
    postData += "&sensor_type=" + String(sensorType);  // 修复：使用正确的传感器类型
    postData += "&data=" + jsonData;  // 修复：单个数据使用data参数
    postData += "&session_id=" + String(session_id);
    postData += "&timestamp=" + String(data.timestamp_ms);

    int httpResponseCode = http.POST(postData);

    bool success = false;
    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.printf("✅ %s 上传成功 (HTTP: %d)\n", sensorType, httpResponseCode);
        success = true;
    } else {
        Serial.printf("❌ %s 上传失败 (HTTP错误: %d)\n", sensorType, httpResponseCode);
        Serial.printf("错误详情: %s\n", http.errorToString(httpResponseCode).c_str());
    }

    http.end();
    return success;
}

// 串口接收任务 - 专注于快速读取数据
void uartReceiveTask(void* parameter) {
    Serial.println("📥 UART接收任务启动");
    uint8_t frame[FRAME_SIZE];
    size_t index = 0;
    uint32_t totalFrameCount = 0;
    uint32_t lastPrintTime = 0;
    uint32_t lastWatchdogReset = 0;

    while (true) {
        // 定期重置看门狗
        uint32_t now = millis();
        if (now - lastWatchdogReset >= 5000) { // 每5秒重置一次
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

                // 将数据放入队列
                if (xQueueSend(dataQueue, &data, 0) == pdTRUE) {
                    totalFrameCount++;
                } else {
                    dataStats.dropped_count[sensorIdx]++;
                    Serial.printf("⚠️ 队列已满，丢弃传感器%d数据帧\n", data.id);
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

// 数据上传任务 - 批量处理队列中的数据，优化内存使用
void dataUploadTask(void* parameter) {
    Serial.println("📤 数据上传任务启动");
    
    // 动态分配批量数组，避免栈溢出
    SensorData* batchData = (SensorData*)malloc(BATCH_SIZE * sizeof(SensorData));
    if (batchData == NULL) {
        Serial.println("❌ 批量数组内存分配失败!");
        vTaskDelete(NULL);
        return;
    }
    
    int batchCount = 0;
    uint32_t lastUploadTime = 0;
    uint32_t totalUploadCount = 0;

    while (true) {
        SensorData data;
        
        // 从队列中获取数据
        if (xQueueReceive(dataQueue, &data, pdMS_TO_TICKS(20)) == pdTRUE) { // 进一步减少等待时间
            // 添加到批量数组
            batchData[batchCount++] = data;
            
            // 当达到批量大小或超过时间间隔时上传
            if (batchCount >= BATCH_SIZE || (millis() - lastUploadTime > 2000 && batchCount > 0)) {
                if (uploadBatchSensorData(batchData, batchCount)) {
                    totalUploadCount += batchCount;
                    Serial.printf("📈 累计上传: %lu 条数据\n", totalUploadCount);
                }
                
                batchCount = 0;
                lastUploadTime = millis();
            }
        } else {
            // 队列为空，检查是否需要上传剩余数据
            if (batchCount > 0 && (millis() - lastUploadTime > 500)) { // 进一步减少等待时间
                if (uploadBatchSensorData(batchData, batchCount)) {
                    totalUploadCount += batchCount;
                    Serial.printf("📈 累计上传: %lu 条数据\n", totalUploadCount);
                }
                batchCount = 0;
                lastUploadTime = millis();
            }
        }
        
        vTaskDelay(pdMS_TO_TICKS(2));  // 进一步减少延迟
    }
    
    // 清理内存（理论上不会执行到这里）
    free(batchData);
}

void setup() {
    Serial.begin(115200);
    Serial1.begin(UART1_BAUD, SERIAL_8N1, UART1_RX, UART1_TX);

    Serial.println("🚀 ESP32 羽毛球传感器数据采集系统启动 (修复版)");
    Serial.println("========================================");
    Serial.printf("队列大小: %d (支持%.1f秒数据缓冲)\n", QUEUE_SIZE, (float)QUEUE_SIZE / 100.0);
    Serial.printf("批量上传大小: %d\n", BATCH_SIZE);
    Serial.printf("支持传感器数量: %d\n", MAX_SENSORS);
    Serial.printf("传感器类型: 1=腰部 2=肩部 3=腕部 4=球拍\n");
    Serial.printf("数据频率: 10ms/帧 (100Hz)\n");
    Serial.printf("批量上传接口: %s\n", server_url);
    Serial.println("========================================");

    // 配置看门狗 - ESP32-S3兼容版本
    esp_task_wdt_config_t wdt_config = {
        .timeout_ms = 30000,  // 30秒超时
        .idle_core_mask = (1 << 0) | (1 << 1),  // 监控两个核心
        .trigger_panic = true  // 启用panic处理
    };
    esp_task_wdt_init(&wdt_config);
    esp_task_wdt_add(NULL);
    Serial.println("✅ 看门狗已配置 (30秒超时)");

    // 创建数据队列
    dataQueue = xQueueCreate(QUEUE_SIZE, sizeof(SensorData));
    if (dataQueue == NULL) {
        Serial.println("❌ 队列创建失败!");
        return;
    }
    Serial.println("✅ 数据队列创建成功");

    // 连接WiFi
    connectWiFi();

    // 启动接收任务 - 高优先级，专注于数据读取
    xTaskCreatePinnedToCore(uartReceiveTask, "UartReceiveTask", 16384, NULL, 3, NULL, 0); // 增大栈空间
    Serial.println("✅ UART接收任务已启动 (核心0, 优先级3, 栈16KB)");

    // 启动上传任务 - 较低优先级，处理网络上传
    xTaskCreatePinnedToCore(dataUploadTask, "DataUploadTask", 16384, NULL, 1, NULL, 1); // 增大栈空间
    Serial.println("✅ 数据上传任务已启动 (核心1, 优先级1, 栈16KB)");
}

void loop() {
    // 主循环处理WiFi重连和状态监控
    static uint32_t lastStatusTime = 0;
    static uint32_t lastWatchdogReset = 0;
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
        Serial.println("=== 系统状态 ===");
        Serial.printf("WiFi状态: %s\n", WiFi.status() == WL_CONNECTED ? "已连接" : "未连接");
        Serial.printf("队列剩余空间: %d\n", uxQueueSpacesAvailable(dataQueue));
        Serial.printf("队列中数据量: %d\n", uxQueueMessagesWaiting(dataQueue));
        
        // 内存信息
        Serial.printf("可用堆内存: %lu bytes\n", ESP.getFreeHeap());
        Serial.printf("最小可用堆内存: %lu bytes\n", ESP.getMinFreeHeap());
        
        // 各传感器统计
        Serial.println("--- 传感器统计 ---");
        const char* sensorNames[] = {"腰部", "肩部", "腕部", "球拍"};
        for (int i = 0; i < MAX_SENSORS; i++) {
            uint32_t sensorId = i + 1;
            uint32_t received = dataStats.received_count[i];
            uint32_t uploaded = dataStats.uploaded_count[i];
            uint32_t dropped = dataStats.dropped_count[i];
            uint32_t lastTime = dataStats.last_receive_time[i];
            
            // 计算数据丢失率
            float lossRate = (received > 0) ? (float)dropped / received * 100.0 : 0.0;
            
            Serial.printf("%s传感器(ID%d): 接收%lu 上传%lu 丢弃%lu(%.1f%%) 最后接收:%lu\n", 
                sensorNames[i], sensorId, received, uploaded, dropped, lossRate, lastTime);
        }
        
        Serial.printf("运行时间: %lu ms\n", now);
        Serial.println("================");
        lastStatusTime = now;
    }
    
    delay(1000);
} 