# 项目结构说明

## 📁 目录结构

```
django-badminton-analysis/
├── 📁 djangodemo/              # Django项目配置
│   ├── __init__.py
│   ├── settings.py             # 项目设置（已优化生产环境）
│   ├── urls.py                 # 主URL配置
│   ├── asgi.py                 # ASGI配置（WebSocket支持）
│   └── wsgi.py                 # WSGI配置
├── 📁 wxapp/                   # 主应用
│   ├── __init__.py
│   ├── models.py               # 数据模型
│   ├── views.py                # API视图
│   ├── urls.py                 # 应用URL配置
│   ├── consumers.py            # WebSocket消费者
│   ├── analysis.py             # 动作分析算法
│   ├── esp32_handler.py        # ESP32数据处理
│   ├── websocket_manager.py    # WebSocket管理
│   ├── admin.py                # 管理后台
│   ├── apps.py                 # 应用配置
│   ├── tests.py                # 测试文件
│   └── 📁 management/          # 管理命令
│       └── commands/
├── 📁 templates/               # HTML模板
│   └── admin/
├── 📁 staticfiles/             # 静态文件（Django收集）
├── 📁 docs/                    # 项目文档
│   ├── API.md                  # API文档
│   ├── DEPLOYMENT.md           # 部署指南
│   ├── DEVELOPMENT.md          # 开发指南
│   ├── ESP32_INTEGRATION.md    # ESP32集成文档
│   └── SENSOR_PEAKS_API.md     # 传感器峰值API文档
├── 📁 wxapp/migrations/        # 数据库迁移文件
├── 📄 README.md                # 项目说明
├── 📄 requirements.txt         # 生产依赖
├── 📄 requirements-dev.txt     # 开发依赖
├── 📄 .gitignore              # Git忽略文件
├── 📄 docker-compose.yml       # Docker开发环境
├── 📄 docker-compose.prod.yml  # Docker生产环境
├── 📄 Dockerfile              # Docker镜像配置
├── 📄 deploy.sh               # 部署脚本
├── 📄 gunicorn.conf.py        # Gunicorn配置
├── 📄 nginx.conf              # Nginx配置
└── 📄 *.ino                   # ESP32固件文件
```

## 🗂️ 文件分类

### 核心文件
- `manage.py` - Django管理脚本
- `djangodemo/` - Django项目配置
- `wxapp/` - 主应用代码
- `requirements.txt` - 生产环境依赖

### 配置文件
- `docker-compose.yml` - 开发环境Docker配置
- `docker-compose.prod.yml` - 生产环境Docker配置
- `Dockerfile` - Docker镜像构建配置
- `nginx.conf` - Nginx反向代理配置
- `gunicorn.conf.py` - Gunicorn WSGI服务器配置

### 部署文件
- `deploy.sh` - 自动部署脚本
- `requirements-dev.txt` - 开发环境依赖

### 文档文件
- `README.md` - 项目概述和快速开始
- `docs/` - 详细文档目录
  - `API.md` - 完整API文档
  - `DEPLOYMENT.md` - 部署指南
  - `DEVELOPMENT.md` - 开发指南
  - `ESP32_INTEGRATION.md` - 硬件集成文档
  - `SENSOR_PEAKS_API.md` - 传感器峰值API文档

### 固件文件
- `esp32s3_multi_sensor_with_timer.ino` - 主固件（推荐）
- `esp32_multi_sensor_fixed.ino` - 兼容版本
- `esp32_wifi_notification_fixed.ino` - WiFi通知版本

## 🚀 快速开始

### 开发环境
```bash
# 1. 克隆项目
git clone <repository-url>
cd django-badminton-analysis

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements-dev.txt

# 4. 数据库迁移
python manage.py migrate

# 5. 启动服务
python manage.py runserver
daphne -b 0.0.0.0 -p 8001 djangodemo.asgi:application
```

### 生产环境
```bash
# 使用Docker部署
docker-compose -f docker-compose.prod.yml up -d

# 或使用传统部署
./deploy.sh
```

## 📋 清理内容

### 已删除的文件
- 所有测试脚本 (`test_*.py`)
- 调试脚本 (`check_*.py`, `analyze_*.py`)
- 临时文件 (`create_*.py`, `simple_*.py`)
- 重复的部署脚本
- 小程序临时文件
- 重复的文档文件
- 过时的配置文件

### 保留的核心文件
- Django核心文件
- 应用代码
- 生产环境配置
- 部署脚本
- 文档文件
- ESP32固件

## 🔧 配置说明

### 环境变量
项目支持通过环境变量配置，主要变量包括：
- `DEBUG` - 调试模式
- `SECRET_KEY` - Django密钥
- `ALLOWED_HOSTS` - 允许的主机
- `DATABASE_URL` - 数据库连接
- `REDIS_URL` - Redis连接

### 安全配置
生产环境已启用：
- HTTPS重定向
- 安全Cookie
- 安全头设置
- CSRF保护

### 日志配置
- 文件日志：`logs/django.log`
- 控制台日志：开发环境DEBUG级别
- 结构化日志格式

## 📊 监控和维护

### 健康检查
- Docker健康检查配置
- 服务状态监控
- 数据库连接检查

### 日志管理
- 结构化日志输出
- 日志轮转配置
- 错误监控集成

### 备份策略
- 数据库自动备份
- 文件系统备份
- 配置备份

## 🎯 下一步

1. **配置环境变量** - 根据实际环境配置
2. **设置域名和SSL** - 配置HTTPS访问
3. **配置监控** - 设置日志和性能监控
4. **测试功能** - 验证所有API和功能
5. **部署到生产** - 使用Docker或传统方式部署
