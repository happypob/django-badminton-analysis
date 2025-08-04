# ESP32接收小程序开始采集消息的流程

## 完整流程图

```
小程序点击"开始采集"
        ↓
POST /wxapp/start_session/
        ↓
POST /wxapp/start_data_collection/
        ↓
POST /wxapp/notify_device_start/
        ↓
后台查找ESP32 IP地址
        ↓
POST http://ESP32_IP/start_collection
        ↓
ESP32接收消息并开始SD卡存储
```

## 详细步骤

### 1. ESP32启动时注册IP
```bash
# ESP32启动后调用
POST /wxapp/register_device_ip/
{
    "device_code": "2025001",
    "ip_address": "192.168.1.100"
}
```

### 2. 小程序开始采集
```bash
# 小程序调用
POST /wxapp/start_session/
{
    "openid": "用户openid",
    "device_group_code": "设备组代码"
}

# 响应
{
    "msg": "session started",
    "session_id": 1011,
    "status": "calibrating"
}
```

### 3. 开始数据采集
```bash
# 小程序调用
POST /wxapp/start_data_collection/
{
    "session_id": 1011
}

# 响应
{
    "msg": "Data collection started",
    "session_id": 1011,
    "status": "collecting"
}
```

### 4. 通知ESP32开始采集
```bash
# 小程序调用
POST /wxapp/notify_device_start/
{
    "session_id": 1011,
    "device_code": "2025001"
}

# 后台自动向ESP32发送
POST http://192.168.1.100/start_collection
{
    "session_id": 1011,
    "device_code": "2025001"
}
```

## ESP32需要实现的端点

### 1. 开始采集端点
```
POST /start_collection
Content-Type: application/x-www-form-urlencoded

参数:
- session_id: 会话ID
- device_code: 设备码

响应:
{
    "msg": "Collection started",
    "session_id": 1011,
    "device_code": "2025001"
}
```

### 2. 停止采集端点
```
POST /stop_collection
Content-Type: application/x-www-form-urlencoded

参数:
- command: "STOP_COLLECTION"

响应:
{
    "msg": "Collection stopped",
    "status": "stopped"
}
```

### 3. 状态查询端点
```
GET /status

响应:
{
    "msg": "Device status",
    "device_code": "2025001",
    "status": "collecting",
    "session_id": 1011
}
```

## 小程序端调用示例

```javascript
// 1. 开始采集会话
wx.request({
  url: 'http://47.122.129.159:8000/wxapp/start_session/',
  method: 'POST',
  data: {
    openid: '用户openid',
    device_group_code: 'test_group_001'
  },
  success: function(res) {
    const sessionId = res.data.session_id;
    
    // 2. 开始数据采集
    wx.request({
      url: 'http://47.122.129.159:8000/wxapp/start_data_collection/',
      method: 'POST',
      data: {
        session_id: sessionId
      },
      success: function(res) {
        
        // 3. 通知ESP32开始采集
        wx.request({
          url: 'http://47.122.129.159:8000/wxapp/notify_device_start/',
          method: 'POST',
          data: {
            session_id: sessionId,
            device_code: '2025001'
          },
          success: function(res) {
            console.log('ESP32通知成功:', res.data);
          }
        });
      }
    });
  }
});
```

## 测试命令

```bash
# 1. 注册ESP32 IP
curl -X POST "http://47.122.129.159:8000/wxapp/register_device_ip/" \
  -d "device_code=2025001&ip_address=192.168.1.100"

# 2. 开始采集会话
curl -X POST "http://47.122.129.159:8000/wxapp/start_session/" \
  -d "openid=test_user&device_group_code=test_group"

# 3. 开始数据采集
curl -X POST "http://47.122.129.159:8000/wxapp/start_data_collection/" \
  -d "session_id=1011"

# 4. 通知ESP32
curl -X POST "http://47.122.129.159:8000/wxapp/notify_device_start/" \
  -d "session_id=1011&device_code=2025001"
```

## 注意事项

1. **ESP32 IP注册**: ESP32必须在启动时注册IP地址
2. **网络连接**: ESP32必须与服务器在同一网络或可访问
3. **设备码统一**: 使用设备码 `2025001`
4. **错误处理**: ESP32应该处理网络错误和重试机制
5. **状态同步**: ESP32应该定期更新状态到服务器

## 故障排除

### 常见问题

1. **ESP32收不到消息**
   - 检查ESP32 IP是否正确注册
   - 检查网络连接
   - 检查ESP32 WebServer是否正常运行

2. **后台通知失败**
   - 检查ESP32 IP地址是否正确
   - 检查ESP32是否响应HTTP请求
   - 检查防火墙设置

3. **会话状态错误**
   - 确保会话在正确的状态
   - 检查会话ID是否正确 