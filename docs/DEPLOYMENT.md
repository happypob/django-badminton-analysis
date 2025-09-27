# 部署指南

## 📋 概述

本指南介绍如何在生产环境中部署羽毛球动作分析系统。

## 🏗️ 系统要求

### 服务器要求
- **操作系统**: Ubuntu 20.04+ / CentOS 7+
- **内存**: 最少 2GB，推荐 4GB+
- **存储**: 最少 20GB，推荐 50GB+
- **网络**: 公网IP，开放80/443端口

### 软件要求
- **Python**: 3.8+
- **Django**: 5.2+
- **Redis**: 6.0+ (用于WebSocket)
- **Nginx**: 1.18+ (反向代理)
- **Docker**: 20.10+ (可选)

## 🚀 快速部署

### 方法一：使用部署脚本

1. **下载并运行部署脚本**:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

2. **配置环境变量**:
   ```bash
   export DEBUG=False
   export SECRET_KEY=your-secret-key
   export ALLOWED_HOSTS=your-domain.com
   ```

3. **启动服务**:
   ```bash
   # 启动Django服务
   python manage.py runserver 0.0.0.0:8000
   
   # 启动WebSocket服务
   daphne -b 0.0.0.0 -p 8001 djangodemo.asgi:application
   ```

### 方法二：使用Docker

1. **构建镜像**:
   ```bash
   docker-compose build
   ```

2. **启动服务**:
   ```bash
   docker-compose up -d
   ```

## ⚙️ 详细配置

### 1. 环境配置

创建 `.env` 文件：
```bash
DEBUG=False
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=your-domain.com,localhost
DATABASE_URL=postgresql://user:password@localhost:5432/badminton_db
REDIS_URL=redis://localhost:6379/0
```

### 2. 数据库配置

#### PostgreSQL (推荐)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'badminton_db',
        'USER': 'badminton_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

#### SQLite (开发环境)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 3. Redis配置

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

### 4. Nginx配置

创建 `/etc/nginx/sites-available/badminton-analysis`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/your/project/staticfiles/;
    }

    location /images/ {
        alias /path/to/your/project/images/;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/badminton-analysis /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔧 生产环境优化

### 1. 安全配置

```python
# settings.py
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# 安全中间件
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# HTTPS设置
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### 2. 性能优化

```python
# 缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# 数据库连接池
DATABASES['default']['CONN_MAX_AGE'] = 60
```

### 3. 日志配置

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/badminton-analysis/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## 📊 监控和维护

### 1. 服务监控

创建 systemd 服务文件 `/etc/systemd/system/badminton-analysis.service`:
```ini
[Unit]
Description=Badminton Analysis Django Application
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/badminton-analysis
Environment=PATH=/opt/badminton-analysis/venv/bin
ExecStart=/opt/badminton-analysis/venv/bin/daphne -b 0.0.0.0 -p 8000 djangodemo.asgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable badminton-analysis.service
sudo systemctl start badminton-analysis.service
```

### 2. 日志管理

```bash
# 查看服务日志
sudo journalctl -u badminton-analysis.service -f

# 查看Nginx日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 3. 备份策略

```bash
# 数据库备份
pg_dump badminton_db > backup_$(date +%Y%m%d).sql

# 文件备份
tar -czf images_backup_$(date +%Y%m%d).tar.gz images/
```

## 🔄 更新部署

### 1. 代码更新

```bash
# 拉取最新代码
git pull origin master

# 安装新依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py migrate

# 收集静态文件
python manage.py collectstatic --noinput

# 重启服务
sudo systemctl restart badminton-analysis.service
```

### 2. 零停机更新

```bash
# 使用Gunicorn + Nginx实现零停机更新
gunicorn --workers 4 --bind 0.0.0.0:8000 djangodemo.wsgi:application
```

## 🐛 故障排除

### 常见问题

1. **端口被占用**:
   ```bash
   sudo lsof -i :8000
   sudo kill -9 <PID>
   ```

2. **权限问题**:
   ```bash
   sudo chown -R www-data:www-data /opt/badminton-analysis
   sudo chmod -R 755 /opt/badminton-analysis
   ```

3. **数据库连接失败**:
   ```bash
   # 检查PostgreSQL状态
   sudo systemctl status postgresql
   
   # 检查连接
   psql -h localhost -U badminton_user -d badminton_db
   ```

4. **Redis连接失败**:
   ```bash
   # 检查Redis状态
   sudo systemctl status redis
   
   # 测试连接
   redis-cli ping
   ```

## 📞 技术支持

如遇到部署问题，请检查：
1. 系统日志：`sudo journalctl -u badminton-analysis.service`
2. Django日志：`tail -f /var/log/badminton-analysis/django.log`
3. Nginx日志：`sudo tail -f /var/log/nginx/error.log`

联系技术支持时请提供：
- 错误日志
- 系统配置信息
- 部署步骤
