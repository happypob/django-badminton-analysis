# 🚀 羽毛球分析系统 WebSocket版本部署指南

## 📋 概述

本指南详细介绍了如何将羽毛球分析系统从旧版本升级到支持WebSocket的新版本。WebSocket提供了更高效的实时双向通信，替代了原有的HTTP+UDP架构。

## 🔄 架构变更对比

### 旧架构（HTTP + UDP）
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

## 🛠️ 部署方案

### 方案1: 快速升级（推荐）

如果您已经在腾讯云服务器上运行了旧版本，可以使用快速升级脚本：

```bash
# 1. 进入项目目录
cd /path/to/your/project

# 2. 给脚本执行权限
chmod +x quick_websocket_upgrade.sh

# 3. 运行升级脚本
./quick_websocket_upgrade.sh
```

### 方案2: 完整重新部署

如果需要完整重新部署：

```bash
# 1. 给脚本执行权限
chmod +x websocket_deploy.sh

# 2. 运行部署脚本
./websocket_deploy.sh
```

## 📦 新增依赖

### 系统依赖
- `redis-server`: WebSocket消息队列
- `nginx`: 反向代理（支持WebSocket）

### Python依赖
```bash
pip install channels[redis] daphne
```

## 🔧 配置变更

### 1. Django设置 (`djangodemo/settings.py`)

```python
# ASGI配置
ASGI_APPLICATION = 'djangodemo.asgi.application'

# Channels配置（使用Redis）
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

### 2. ASGI配置 (`djangodemo/asgi.py`)

```python
import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import wxapp.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangodemo.settings')
django.setup()

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            wxapp.routing.websocket_urlpatterns
        )
    ),
})
```

### 3. Nginx配置

```nginx
server {
    listen 80;
    server_name _;
    
    # WebSocket支持
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
    
    # HTTP代理
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. Systemd服务配置

```ini
[Unit]
Description=Badminton Analysis Django Application (WebSocket)
After=network.target redis-server.service

[Service]
Type=simple
User=your-username
Group=your-username
WorkingDirectory=/path/to/your/project
Environment=PATH=/path/to/your/project/venv/bin
Environment=DJANGO_SETTINGS_MODULE=djangodemo.settings
ExecStart=/path/to/your/project/venv/bin/daphne -b 0.0.0.0 -p 8000 djangodemo.asgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 🔌 WebSocket端点

### ESP32设备连接
- **URL**: `ws://your-domain:8000/ws/esp32/{device_code}/`
- **消息类型**:
  - `heartbeat` - 心跳消息
  - `poll_commands` - 轮询服务器指令
  - `status_update` - 状态更新
  - `sensor_data` - 单条传感器数据
  - `batch_sensor_data` - 批量传感器数据
  - `upload_complete` - 数据上传完成

### 小程序连接
- **URL**: `ws://your-domain:8000/ws/miniprogram/{user_id}/`
- **消息类型**:
  - `session_status` - 查询会话状态
  - `analysis_complete_notification` - 分析完成通知

### 管理后台连接
- **URL**: `ws://your-domain:8000/ws/admin/`
- **消息类型**:
  - `get_system_status` - 获取系统状态
  - `get_device_list` - 获取设备列表
  - `system_notification` - 系统通知

## 🚀 部署步骤详解

### 1. 准备工作

```bash
# 确保在项目根目录
cd /path/to/your/project

# 检查Git仓库状态
git status

# 备份当前版本（可选）
cp -r . ../backup-$(date +%Y%m%d)
```

### 2. 停止现有服务

```bash
# 停止Django服务
sudo systemctl stop badminton-analysis.service

# 停止其他相关进程
sudo pkill -f "python manage.py runserver"
sudo pkill -f "gunicorn"
```

### 3. 安装Redis

```bash
# 安装Redis
sudo apt update
sudo apt install -y redis-server

# 启动Redis服务
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 检查Redis状态
sudo systemctl status redis-server
```

### 4. 更新代码和依赖

```bash
# 拉取最新代码
git pull origin master

# 激活虚拟环境
source venv/bin/activate

# 安装新依赖
pip install channels[redis] daphne

# 执行数据库迁移
python manage.py makemigrations
python manage.py migrate

# 收集静态文件
python manage.py collectstatic --noinput
```

### 5. 配置服务

```bash
# 更新systemd服务文件
sudo systemctl daemon-reload

# 更新Nginx配置
sudo nginx -t
sudo systemctl restart nginx

# 启动服务
sudo systemctl start badminton-analysis.service
sudo systemctl enable badminton-analysis.service
```

### 6. 验证部署

```bash
# 检查服务状态
sudo systemctl status badminton-analysis.service

# 检查WebSocket连接
curl -I http://localhost:8000/

# 查看日志
sudo journalctl -u badminton-analysis.service -f
```

## 🔍 测试WebSocket连接

### 使用浏览器测试

1. 打开浏览器开发者工具
2. 在控制台中运行：

```javascript
// 测试ESP32连接
const ws = new WebSocket('ws://your-domain:8000/ws/esp32/TEST_DEVICE/');
ws.onopen = () => console.log('连接成功');
ws.onmessage = (event) => console.log('收到消息:', event.data);
ws.onclose = () => console.log('连接关闭');
```

### 使用Python测试

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://your-domain:8000/ws/esp32/TEST_DEVICE/"
    async with websockets.connect(uri) as websocket:
        # 发送心跳
        await websocket.send(json.dumps({
            "type": "heartbeat",
            "timestamp": 1234567890
        }))
        
        # 接收响应
        response = await websocket.recv()
        print(f"收到响应: {response}")

asyncio.run(test_websocket())
```

## 🛠️ 故障排除

### 常见问题

1. **Redis连接失败**
   ```bash
   # 检查Redis状态
   sudo systemctl status redis-server
   
   # 重启Redis
   sudo systemctl restart redis-server
   ```

2. **WebSocket连接失败**
   ```bash
   # 检查Nginx配置
   sudo nginx -t
   
   # 检查防火墙
   sudo ufw status
   sudo ufw allow 8000
   ```

3. **服务启动失败**
   ```bash
   # 查看详细日志
   sudo journalctl -u badminton-analysis.service -n 50
   
   # 检查端口占用
   sudo netstat -tlnp | grep 8000
   ```

### 回滚方案

如果升级后出现问题，可以快速回滚：

```bash
# 恢复Git状态
git stash pop

# 或者重新部署旧版本
git checkout <old-commit-hash>
./server_deploy.sh
```

## 📊 性能优化

### Redis配置优化

编辑 `/etc/redis/redis.conf`：

```conf
# 内存优化
maxmemory 256mb
maxmemory-policy allkeys-lru

# 持久化
save 900 1
save 300 10
save 60 10000
```

### Nginx优化

在nginx配置中添加：

```nginx
# 连接优化
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;

# 缓冲优化
proxy_buffering on;
proxy_buffer_size 4k;
proxy_buffers 8 4k;
```

## 📝 监控和维护

### 日志监控

```bash
# 实时查看服务日志
sudo journalctl -u badminton-analysis.service -f

# 查看Nginx访问日志
sudo tail -f /var/log/nginx/access.log

# 查看Redis日志
sudo tail -f /var/log/redis/redis-server.log
```

### 性能监控

```bash
# 检查系统资源
htop

# 检查网络连接
netstat -tlnp

# 检查Redis内存使用
redis-cli info memory
```

## 🎉 部署完成

部署完成后，您将拥有：

- ✅ 支持WebSocket的实时通信
- ✅ 更高效的设备连接管理
- ✅ 更好的用户体验
- ✅ 完整的监控和日志系统

您的系统现在可以支持ESP32设备的实时WebSocket连接，提供更稳定和高效的通信体验！ 