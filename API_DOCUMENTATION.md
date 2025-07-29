# 羽毛球动作分析系统 API 文档

## 📋 概述

本系统为羽毛球动作分析提供完整的后端API支持，包括微信用户管理、设备绑定、数据采集、动作分析等功能。

**基础URL**: `http://127.0.0.1:8000`  
**API前缀**: `/wxapp`

---

## 🔐 用户认证

### 微信用户登录
```
POST /wxapp/login/
```

**功能**: 通过微信小程序code获取用户openid并创建用户

**请求参数**:
- `code` (string, 必需): 微信小程序登录code

**请求示例**:
```javascript
wx.request({
  url: 'http://127.0.0.1:8000/wxapp/login/',
  method: 'POST',
  data: {
    code: 'wx_login_code_here'
  },
  success: function(res) {
    console.log(res.data);
  }
});
```

**响应示例**:
```json
{
  "msg": "ok",
  "openid": "wx_user_openid_123",
  "user_id": 1
}
```

**错误响应**:
```json
{
  "error": "WeChat auth failed",
  "detail": {"errcode": 40013, "errmsg": "invalid appid"}
}
```

---

## 📱 设备管理

### 绑定设备
```
POST /wxapp/bind_device/
```

**功能**: 将设备与用户绑定

**请求参数**:
- `openid` (string, 必需): 用户openid
- `device_code` (string, 必需): 设备编码

**请求示例**:
```javascript
wx.request({
  url: 'http://127.0.0.1:8000/wxapp/bind_device/',
  method: 'POST',
  data: {
    openid: 'wx_user_openid_123',
    device_code: 'sensor_device_001'
  }
});
```

**响应示例**:
```json
{
  "msg": "device bind success"
}
```

---

## 📊 数据采集会话

### 开始数据采集会话
```
POST /wxapp/start_session/
```

**功能**: 开始一个新的数据采集会话

**请求参数**:
- `openid` (string, 必需): 用户openid
- `device_group_code` (string, 必需): 设备组编码

**请求示例**:
```javascript
wx.request({
  url: 'http://127.0.0.1:8000/wxapp/start_session/',
  method: 'POST',
  data: {
    openid: 'wx_user_openid_123',
    device_group_code: 'badminton_group_001'
  }
});
```

**响应示例**:
```json
{
  "msg": "session started",
  "session_id": 123,
  "status": "calibrating",
  "calibration_command": "CALIBRATE_badminton_group_001"
}
```

### 结束数据采集会话
```
POST /wxapp/end_session/
```

**功能**: 结束数据采集会话并开始分析

**请求参数**:
- `session_id` (integer, 必需): 会话ID

**请求示例**:
```javascript
wx.request({
  url: 'http://127.0.0.1:8000/wxapp/end_session/',
  method: 'POST',
  data: {
    session_id: 123
  }
});
```

**响应示例**:
```json
{
  "msg": "session ended and analysis started",
  "analysis_id": 456,
  "status": "analyzing"
}
```

---

## 📡 传感器数据上传

### 上传传感器数据
```
POST /wxapp/upload_sensor_data/
```

**功能**: 上传传感器采集的数据

**请求参数**:
- `session_id` (integer, 可选): 会话ID（如果有会话）
- `device_code` (string, 必需): 设备编码
- `sensor_type` (string, 必需): 传感器类型 (waist/shoulder/wrist/racket)
- `data` (string, 必需): 传感器数据（JSON格式）

**数据格式**:
```json
{
  "acc": [1.2, 0.8, 9.8],      // 加速度XYZ
  "gyro": [0.1, 0.2, 0.3],     // 角速度XYZ
  "angle": [45.0, 30.0, 60.0], // 角度XYZ
  "timestamp": 1640995200       // 时间戳
}
```

**请求示例**:
```javascript
const sensorData = {
  acc: [1.2, 0.8, 9.8],
  gyro: [0.1, 0.2, 0.3],
  angle: [45.0, 30.0, 60.0],
  timestamp: Date.now()
};

wx.request({
  url: 'http://127.0.0.1:8000/wxapp/upload_sensor_data/',
  method: 'POST',
  data: {
    session_id: 123,
    device_code: 'waist_sensor_001',
    sensor_type: 'waist',
    data: JSON.stringify(sensorData)
  }
});
```

**响应示例**:
```json
{
  "msg": "data upload success",
  "data_id": 789
}
```

---

## 📈 分析结果

### 获取分析结果
```
GET /wxapp/get_analysis/
```

**功能**: 获取会话的分析结果

**请求参数**:
- `session_id` (integer, 必需): 会话ID

**请求示例**:
```javascript
wx.request({
  url: 'http://127.0.0.1:8000/wxapp/get_analysis/',
  method: 'GET',
  data: {
    session_id: 123
  }
});
```

**响应示例**:
```json
{
  "msg": "analysis result",
  "phase_delay": {
    "waist_to_shoulder": 0.08,
    "shoulder_to_wrist": 0.05
  },
  "energy_ratio": 0.75,
  "rom_data": {
    "waist": 45,
    "shoulder": 120,
    "wrist": 45
  }
}
```

### 生成详细分析报告
```
GET /wxapp/generate_report/
```

**功能**: 生成详细的分析报告，包含评分和建议

**请求参数**:
- `session_id` (integer, 必需): 会话ID

**请求示例**:
```javascript
wx.request({
  url: 'http://127.0.0.1:8000/wxapp/generate_report/',
  method: 'GET',
  data: {
    session_id: 123
  }
});
```

**响应示例**:
```json
{
  "msg": "analysis report",
  "report": {
    "summary": "动作表现良好，时序协调性优秀",
    "recommendations": [
      "建议加快腰部到肩部的发力转换速度",
      "建议提高能量传递效率"
    ],
    "scores": {
      "delay_score": 85,
      "energy_score": 90,
      "rom_score": 88
    }
  },
  "session_info": {
    "start_time": "2025-07-10T11:30:00",
    "end_time": "2025-07-10T11:35:00",
    "status": "completed"
  }
}
```

---

## 📁 .mat文件上传

### 上传.mat文件
```
POST /wxapp/upload_mat/
```

**功能**: 上传.mat文件进行批量分析

**请求参数**:
- `mat_file` (file, 必需): .mat文件
- `openid` (string, 必需): 用户openid

**请求示例**:
```javascript
wx.chooseMessageFile({
  count: 1,
  type: 'file',
  success: function(res) {
    const tempFilePath = res.tempFiles[0].path;
    
    wx.uploadFile({
      url: 'http://127.0.0.1:8000/wxapp/upload_mat/',
      filePath: tempFilePath,
      name: 'mat_file',
      formData: {
        openid: 'wx_user_openid_123'
      },
      success: function(res) {
        console.log(JSON.parse(res.data));
      }
    });
  }
});
```

**响应示例**:
```json
{
  "msg": "mat file processed successfully",
  "session_id": 456,
  "data_summary": {
    "total_sensor_records": 300,
    "sensor_records": {
      "waist": 100,
      "shoulder": 100,
      "wrist": 100
    },
    "analysis_id": 789
  }
}
```

### 获取.mat文件分析结果
```
GET /wxapp/get_mat_analysis/
```

**功能**: 获取.mat文件的分析结果

**请求参数**:
- `session_id` (integer, 必需): 会话ID

**请求示例**:
```javascript
wx.request({
  url: 'http://127.0.0.1:8000/wxapp/get_mat_analysis/',
  method: 'GET',
  data: {
    session_id: 456
  }
});
```

**响应示例**:
```json
{
  "msg": "mat analysis result",
  "report": {
    "summary": "动作分析完成",
    "recommendations": [
      "建议提高动作连贯性",
      "建议增加腰部旋转幅度"
    ],
    "scores": {
      "delay_score": 82,
      "energy_score": 85,
      "rom_score": 78
    }
  },
  "session_info": {
    "start_time": "2025-07-10T11:30:00",
    "end_time": "2025-07-10T11:35:00",
    "status": "completed"
  }
}
```

---

## 🚀 完整使用流程

### 1. 实时数据采集流程
```javascript
// 1. 用户登录
wx.login({
  success: function(res) {
    wx.request({
      url: 'http://127.0.0.1:8000/wxapp/login/',
      method: 'POST',
      data: { code: res.code },
      success: function(loginRes) {
        const openid = loginRes.data.openid;
        
        // 2. 开始会话
        wx.request({
          url: 'http://127.0.0.1:8000/wxapp/start_session/',
          method: 'POST',
          data: {
            openid: openid,
            device_group_code: 'badminton_group_001'
          },
          success: function(sessionRes) {
            const sessionId = sessionRes.data.session_id;
            
            // 3. 上传传感器数据（循环）
            function uploadSensorData() {
              const sensorData = {
                acc: [1.2, 0.8, 9.8],
                gyro: [0.1, 0.2, 0.3],
                angle: [45.0, 30.0, 60.0],
                timestamp: Date.now()
              };
              
              wx.request({
                url: 'http://127.0.0.1:8000/wxapp/upload_sensor_data/',
                method: 'POST',
                data: {
                  session_id: sessionId,
                  device_code: 'waist_sensor_001',
                  sensor_type: 'waist',
                  data: JSON.stringify(sensorData)
                }
              });
            }
            
            // 4. 结束会话
            wx.request({
              url: 'http://127.0.0.1:8000/wxapp/end_session/',
              method: 'POST',
              data: { session_id: sessionId },
              success: function() {
                // 5. 获取分析结果
                wx.request({
                  url: 'http://127.0.0.1:8000/wxapp/get_analysis/',
                  method: 'GET',
                  data: { session_id: sessionId },
                  success: function(analysisRes) {
                    console.log('分析结果:', analysisRes.data);
                  }
                });
              }
            });
          }
        });
      }
    });
  }
});
```

### 2. .mat文件上传流程
```javascript
// 1. 选择.mat文件
wx.chooseMessageFile({
  count: 1,
  type: 'file',
  success: function(res) {
    const tempFilePath = res.tempFiles[0].path;
    
    // 2. 上传文件
    wx.uploadFile({
      url: 'http://127.0.0.1:8000/wxapp/upload_mat/',
      filePath: tempFilePath,
      name: 'mat_file',
      formData: {
        openid: 'wx_user_openid_123'
      },
      success: function(res) {
        const result = JSON.parse(res.data);
        const sessionId = result.session_id;
        
        // 3. 获取分析结果
        wx.request({
          url: 'http://127.0.0.1:8000/wxapp/get_mat_analysis/',
          method: 'GET',
          data: { session_id: sessionId },
          success: function(analysisRes) {
            console.log('分析结果:', analysisRes.data);
          }
        });
      }
    });
  }
});
```

---

## ⚠️ 错误处理

所有API在出错时会返回以下格式：
```json
{
  "error": "错误描述信息"
}
```

常见错误码：
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

---

## 📝 注意事项

1. **数据格式**: 传感器数据必须为JSON格式字符串
2. **文件上传**: .mat文件必须包含'allData'字段
3. **会话管理**: 必须先开始会话才能上传数据
4. **设备编码**: 传感器设备编码已固定为 `waist_sensor_001`、`shoulder_sensor_001`、`wrist_sensor_001`
5. **时间戳**: 建议使用毫秒级时间戳

---

## 🧪 测试工具

使用提供的测试脚本进行API测试：
```bash
# 运行完整测试
python test_miniprogram_api_simple.py

# 运行单个测试
python test_miniprogram_api_simple.py start_session
python test_miniprogram_api_simple.py upload_sensor_data
python test_miniprogram_api_simple.py upload_mat
``` 