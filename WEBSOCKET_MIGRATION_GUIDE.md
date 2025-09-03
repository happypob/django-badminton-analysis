# 羽毛球分析系统 WebSocket 迁移指南

## 概述

本指南详细介绍了将ESP32通信从HTTP协议迁移到WebSocket协议的完整过程。WebSocket提供了更加实时、高效的双向通信机制，相比HTTP轮询具有更低的延迟和更好的连接稳定性。

## 🔧 技术架构变更

### 原架构（HTTP + UDP）
```
小程序 ←→ Django后端 ←→ ESP32
                ↓
              UDP广播
```

### 新架构（WebSocket）
```
小程序 ←→ Django后端 ←→ ESP32
    ↑         ↑         ↑
  WebSocket WebSocket WebSocket
```

## 📦 新增依赖

在 `requirements.txt` 中添加了以下WebSocket支持包：

```
channels>=4.0.0
channels-redis>=4.1.0
daphne>=4.0.0
```

## 🏗️ 核心组件

### 1. WebSocket路由配置 (`wxapp/routing.py`)

定义了三种类型的WebSocket连接：
- **ESP32设备连接**: `ws/esp32/{device_code}/`
- **小程序用户连接**: `ws/miniprogram/{user_id}/`
- **管理后台连接**: `ws/admin/`

### 2. WebSocket消费者 (`wxapp/consumers.py`)

#### ESP32Consumer
- 处理ESP32设备的WebSocket连接
- 支持心跳、轮询指令、状态更新、传感器数据上传
- 自动注册/注销设备连接状态

#### MiniProgramConsumer
- 处理小程序的WebSocket连接
- 接收分析完成通知
- 查询会话状态

#### AdminConsumer
- 处理管理后台的WebSocket连接
- 系统状态监控
- 设备列表管理

### 3. WebSocket连接管理器 (`wxapp/websocket_manager.py`)

提供统一的WebSocket消息发送和连接管理：
- `send_to_device()` - 向指定ESP32设备发送消息
- `send_to_user()` - 向指定小程序用户发送消息
- `broadcast_to_devices()` - 向所有设备广播消息
- `register_device()` / `unregister_device()` - 设备连接管理

### 4. Django配置更新

#### `djangodemo/settings.py`
```python
INSTALLED_APPS = [
    # ... 其他应用
    'channels',
    'wxapp',
]

# ASGI配置用于WebSocket
ASGI_APPLICATION = 'djangodemo.asgi.application'

# Channels配置
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}
```

#### `djangodemo/asgi.py`
```python
application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            wxapp.routing.websocket_urlpatterns
        )
    ),
})
```

## 🔄 功能迁移对比

| 功能 | 原实现（HTTP/UDP） | 新实现（WebSocket） |
|------|-------------------|-------------------|
| 设备指令下发 | UDP广播 | WebSocket直推 |
| 设备状态查询 | HTTP请求 | WebSocket连接状态 |
| 数据上传 | HTTP POST | WebSocket消息 |
| 实时通知 | HTTP轮询 | WebSocket推送 |
| 连接管理 | 静态IP映射 | 动态连接管理 |

## 🔗 WebSocket端点

### ESP32设备端点
- **URL**: `ws://your-domain/ws/esp32/{device_code}/`
- **消息类型**:
  - `heartbeat` - 心跳消息
  - `poll_commands` - 轮询服务器指令
  - `status_update` - 状态更新
  - `sensor_data` - 单条传感器数据
  - `batch_sensor_data` - 批量传感器数据
  - `upload_complete` - 数据上传完成

### 小程序端点
- **URL**: `ws://your-domain/ws/miniprogram/{user_id}/`
- **消息类型**:
  - `session_status` - 查询会话状态
  - `analysis_complete_notification` - 分析完成通知（服务器推送）

### 管理后台端点
- **URL**: `ws://your-domain/ws/admin/`
- **消息类型**:
  - `get_system_status` - 获取系统状态
  - `get_device_list` - 获取设备列表
  - `system_notification` - 系统通知（服务器推送）

## 📝 API变更

### 后端接口更新

原有的HTTP接口保持兼容，但内部实现已改为WebSocket：

1. **设备通知接口** - 从HTTP请求改为WebSocket消息推送
2. **UDP广播** - 替换为WebSocket广播
3. **设备状态查询** - 从HTTP状态检查改为WebSocket连接状态

### 工具函数更新

在 `websocket_manager.py` 中提供了替代函数：
- `send_esp32_start_command()` - 替代HTTP开始指令
- `send_esp32_stop_command()` - 替代HTTP停止指令
- `check_esp32_connection()` - 替代HTTP连接检查
- `get_esp32_status()` - 替代HTTP状态查询

## 🧪 测试和验证

### WebSocket测试页面
访问 `http://your-domain/websocket-test/` 可以进行完整的WebSocket功能测试，包括：
- ESP32设备连接测试
- 小程序连接测试
- 管理后台连接测试
- 各种消息类型的发送测试

### 测试步骤
1. 启动Django服务器（支持WebSocket）
2. 访问测试页面
3. 分别测试三种类型的WebSocket连接
4. 验证消息发送和接收功能

## 🚀 部署说明

### 开发环境
```bash
# 安装依赖
pip install -r requirements.txt

# 运行开发服务器（自动支持WebSocket）
python manage.py runserver
```

### 生产环境

#### 使用Daphne（推荐）
```bash
# 安装daphne
pip install daphne

# 启动ASGI服务器
daphne -b 0.0.0.0 -p 8000 djangodemo.asgi:application
```

#### 使用Nginx代理
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 💡 最佳实践

### 1. 连接管理
- 设备连接时自动注册到websocket_manager
- 断开连接时自动注销
- 定期发送心跳消息保持连接活跃

### 2. 错误处理
- WebSocket连接异常时的重连机制
- 消息发送失败的重试逻辑
- 连接状态的实时监控

### 3. 性能优化
- 使用Redis作为Channel Layer（生产环境）
- 批量处理传感器数据
- 合理设置WebSocket超时时间

### 4. 安全考虑
- WebSocket连接认证
- 消息内容验证
- 防止恶意连接攻击

## 🔍 监控和调试

### 日志记录
系统会记录以下WebSocket相关日志：
- 设备连接/断开事件
- 消息发送成功/失败
- 数据分析触发和完成
- 系统异常和错误

### 调试工具
- 浏览器开发者工具的Network标签（WebSocket连接）
- Django Admin中的连接状态监控
- WebSocket测试页面的实时日志

## 🆕 新功能特性

### 1. 实时通知
- 分析完成后立即通知小程序用户
- 设备状态变化实时推送给管理后台
- 系统事件的实时广播

### 2. 连接状态管理
- 实时显示设备在线状态
- 连接质量监控
- 自动重连机制

### 3. 双向通信
- 服务器主动推送指令给ESP32
- ESP32实时上报状态和数据
- 小程序实时接收分析结果

## 🔧 故障排除

### 常见问题

1. **WebSocket连接失败**
   - 检查Django settings中的ASGI配置
   - 确认channels包已正确安装
   - 验证路由配置是否正确

2. **消息发送失败**
   - 检查设备是否已连接
   - 验证消息格式是否正确
   - 查看服务器日志获取详细错误信息

3. **性能问题**
   - 考虑使用Redis作为Channel Layer
   - 优化消息处理逻辑
   - 减少不必要的消息发送

### 兼容性说明
- 保持原有HTTP接口的兼容性
- UDP广播功能作为备用方案保留
- 可以逐步迁移，不影响现有功能

## 📚 参考文档
- [Django Channels官方文档](https://channels.readthedocs.io/)
- [WebSocket协议规范](https://tools.ietf.org/html/rfc6455)
- [Daphne部署指南](https://github.com/django/daphne) 