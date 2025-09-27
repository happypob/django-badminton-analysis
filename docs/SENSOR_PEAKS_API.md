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

```javascript
// 微信小程序中调用
wx.request({
  url: 'http://127.0.0.1:8000/wxapp/get_sensor_peaks/',
  method: 'GET',
  data: {
    session_id: 123
  },
  success: function(res) {
    console.log('峰值数据:', res.data);
  }
});
```

## 响应格式

### 成功响应

```json
{
  "msg": "success",
  "data": {
    "waist": {
      "peak_angular_velocity": 45.2,
      "timestamp": "2025-01-10T10:30:15.123Z"
    },
    "shoulder": {
      "peak_angular_velocity": 38.7,
      "timestamp": "2025-01-10T10:30:16.456Z"
    },
    "wrist": {
      "peak_angular_velocity": 52.1,
      "timestamp": "2025-01-10T10:30:17.789Z"
    }
  }
}
```

### 错误响应

```json
{
  "error": "Session not found"
}
```

## 数据说明

### 峰值合角速度计算

峰值合角速度通过以下公式计算：

```
合角速度 = √(ωx² + ωy² + ωz²)
```

其中：
- ωx, ωy, ωz 分别是X、Y、Z轴的角速度
- 峰值是指在数据采集期间的最大合角速度值

### 传感器类型

| 传感器 | 描述 | 典型峰值范围 |
|--------|------|-------------|
| waist | 腰部传感器 | 20-60 rad/s |
| shoulder | 肩部传感器 | 15-50 rad/s |
| wrist | 腕部传感器 | 25-70 rad/s |

## 使用场景

### 1. 柱状图显示

```javascript
// 使用ECharts绘制柱状图
const option = {
  title: {
    text: '传感器峰值合角速度'
  },
  xAxis: {
    data: ['腰部', '肩部', '腕部']
  },
  yAxis: {
    type: 'value',
    name: '合角速度 (rad/s)'
  },
  series: [{
    type: 'bar',
    data: [
      res.data.waist.peak_angular_velocity,
      res.data.shoulder.peak_angular_velocity,
      res.data.wrist.peak_angular_velocity
    ]
  }]
};
```

### 2. 性能对比

```javascript
// 计算相对性能
const waistPeak = res.data.waist.peak_angular_velocity;
const shoulderPeak = res.data.shoulder.peak_angular_velocity;
const wristPeak = res.data.wrist.peak_angular_velocity;

const maxPeak = Math.max(waistPeak, shoulderPeak, wristPeak);

const performance = {
  waist: (waistPeak / maxPeak * 100).toFixed(1) + '%',
  shoulder: (shoulderPeak / maxPeak * 100).toFixed(1) + '%',
  wrist: (wristPeak / maxPeak * 100).toFixed(1) + '%'
};
```

## 错误处理

### 常见错误

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| Session not found | 会话ID不存在 | 检查session_id是否正确 |
| No sensor data | 会话中没有传感器数据 | 确保数据已上传 |
| Analysis not completed | 分析未完成 | 等待分析完成后再调用 |

### 错误处理示例

```javascript
wx.request({
  url: 'http://127.0.0.1:8000/wxapp/get_sensor_peaks/',
  method: 'GET',
  data: { session_id: 123 },
  success: function(res) {
    if (res.data.msg === 'success') {
      // 处理成功数据
      displayPeakData(res.data.data);
    } else {
      // 处理错误
      wx.showToast({
        title: res.data.error || '获取数据失败',
        icon: 'none'
      });
    }
  },
  fail: function(err) {
    wx.showToast({
      title: '网络错误',
      icon: 'none'
    });
  }
});
```

## 性能优化

### 1. 缓存策略

```javascript
// 使用本地缓存
const cacheKey = `sensor_peaks_${sessionId}`;
const cachedData = wx.getStorageSync(cacheKey);

if (cachedData) {
  // 使用缓存数据
  displayPeakData(cachedData);
} else {
  // 从服务器获取
  fetchPeakData(sessionId);
}
```

### 2. 数据验证

```javascript
function validatePeakData(data) {
  const requiredSensors = ['waist', 'shoulder', 'wrist'];
  
  for (const sensor of requiredSensors) {
    if (!data[sensor] || typeof data[sensor].peak_angular_velocity !== 'number') {
      return false;
    }
  }
  
  return true;
}
```

## 注意事项

1. **数据时效性**: 峰值数据在分析完成后才会生成
2. **精度要求**: 角速度数据保留2位小数
3. **单位统一**: 所有角速度数据使用rad/s单位
4. **异常处理**: 建议添加超时和重试机制

## 更新日志

- v1.0.0: 初始版本，支持基本峰值数据获取
- v1.1.0: 添加时间戳信息
- v1.2.0: 优化错误处理机制
