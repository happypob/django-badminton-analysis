# 传感器峰值合角速度API指南

## 概述

这个API用于获取三个传感器（腰部、肩部、腕部）的峰值合角速度数据，主要用于前端绘制柱状图显示各传感器的峰值表现。

## API端点

```
GET /wxapp/get_sensor_peaks/
```

## 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| session_id | int | 是 | 数据采集会话ID |

## 请求示例

```bash
curl "http://localhost:8000/wxapp/get_sensor_peaks/?session_id=1"
```

```javascript
// 前端JavaScript调用示例
const response = await fetch('/wxapp/get_sensor_peaks/?session_id=1');
const data = await response.json();
```

## 响应格式

### 成功响应 (200)

```json
{
    "msg": "sensor peaks data",
    "waist_peak": 45.2,
    "shoulder_peak": 38.7,
    "wrist_peak": 52.1,
    "peaks": {
        "waist": 45.2,
        "shoulder": 38.7,
        "wrist": 52.1
    },
    "data": [45.2, 38.7, 52.1],
    "session_info": {
        "session_id": 1,
        "start_time": "2024-01-01T10:00:00Z",
        "end_time": "2024-01-01T10:05:00Z",
        "status": "completed"
    }
}
```

### 错误响应

#### 400 Bad Request
```json
{
    "error": "session_id required"
}
```

#### 404 Not Found
```json
{
    "error": "Session not found"
}
```

```json
{
    "error": "No sensor data found for this session"
}
```

#### 500 Internal Server Error
```json
{
    "error": "Analysis failed: [具体错误信息]"
}
```

## 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| msg | string | 响应消息 |
| waist_peak | float | 腰部传感器峰值合角速度 (rad/s) |
| shoulder_peak | float | 肩部传感器峰值合角速度 (rad/s) |
| wrist_peak | float | 腕部传感器峰值合角速度 (rad/s) |
| peaks | object | 峰值数据对象，包含三个传感器的峰值 |
| data | array | 峰值数据数组 [腰部, 肩部, 腕部] |
| session_info | object | 会话信息 |

## 前端兼容性

该API设计为与现有前端代码完全兼容。前端代码支持多种数据格式：

```javascript
// 前端解析逻辑（宽松解析）
let waist = result && (result.waist_peak || result.waist || (result.peaks && (result.peaks.waist || result.peaks.waist_peak)));
let shoulder = result && (result.shoulder_peak || result.shoulder || (result.peaks && (result.peaks.shoulder || result.peaks.shoulder_peak)));
let wrist = result && (result.wrist_peak || result.wrist || (result.peaks && (result.peaks.wrist || result.peaks.wrist_peak)));

if (Array.isArray(result && result.data) && result.data.length >= 3) {
    waist = waist ?? result.data[0];
    shoulder = shoulder ?? result.data[1];
    wrist = wrist ?? result.data[2];
}
```

## 峰值计算算法

1. **合角速度计算**: 对每个传感器的三轴角速度数据计算合角速度
   ```
   magnitude = sqrt(gyro_x² + gyro_y² + gyro_z²)
   ```

2. **峰值检测**: 使用scipy的find_peaks函数检测峰值
   - 腰部: height=10, prominence=5, distance=20ms
   - 肩部: height=8, prominence=3, distance=20ms  
   - 腕部: height=12, prominence=5, distance=20ms

3. **峰值选择**: 如果检测到多个峰值，选择最大值；如果没有检测到峰值，使用整个序列的最大值

## 使用场景

- 前端柱状图显示各传感器峰值表现
- 动作分析中的峰值对比
- 训练效果评估
- 实时数据监控

## 注意事项

1. 确保会话已完成数据采集且有有效的传感器数据
2. 峰值计算基于角速度的合角速度，单位为rad/s
3. 如果某个传感器没有数据，对应峰值将返回0.0
4. API会自动处理ESP32时间戳和服务器时间戳的优先级

## 测试

使用提供的测试脚本进行API测试：

```bash
python test_sensor_peaks_api.py
```

确保Django服务器正在运行：

```bash
python manage.py runserver
```
