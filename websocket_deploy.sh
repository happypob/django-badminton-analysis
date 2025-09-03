#!/bin/bash

# 羽毛球分析系统 - WebSocket版本部署脚本
# 适用于从旧版本升级到WebSocket版本

set -e  # 遇到错误立即退出

echo "🚀 开始部署羽毛球分析系统 WebSocket版本..."
echo "================================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. 检查当前目录
if [ ! -f "manage.py" ]; then
    log_error "请在项目根目录运行此脚本"
    exit 1
fi

# 2. 备份当前版本
log_info "📦 备份当前版本..."
BACKUP_DIR="/opt/badminton-analysis-backup-$(date +%Y%m%d-%H%M%S)"
sudo mkdir -p "$BACKUP_DIR"
sudo cp -r . "$BACKUP_DIR/"
log_success "备份完成: $BACKUP_DIR"

# 3. 停止现有服务
log_info "🛑 停止现有服务..."
sudo systemctl stop badminton-analysis.service 2>/dev/null || true
sudo pkill -f "python manage.py runserver" 2>/dev/null || true
sudo pkill -f "gunicorn" 2>/dev/null || true
sudo pkill -f "daphne" 2>/dev/null || true

# 4. 更新系统包
log_info "📦 更新系统包..."
sudo apt update
sudo apt upgrade -y

# 5. 安装WebSocket相关依赖
log_info "🔧 安装WebSocket相关依赖..."
sudo apt install -y python3 python3-pip python3-venv nginx redis-server

# 6. 启动Redis服务（WebSocket需要）
log_info "🔴 启动Redis服务..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 7. 更新项目代码
log_info "📥 更新项目代码..."
if [ -d ".git" ]; then
    git pull origin master
    log_success "代码更新完成"
else
    log_warning "未检测到Git仓库，请确保代码是最新版本"
fi

# 8. 更新Python依赖
log_info "🐍 更新Python依赖..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 安装额外的WebSocket依赖
pip install channels[redis] daphne

log_success "Python依赖安装完成"

# 9. 数据库迁移
log_info "🗄️ 执行数据库迁移..."
python manage.py makemigrations
python manage.py migrate
log_success "数据库迁移完成"

# 10. 收集静态文件
log_info "📦 收集静态文件..."
python manage.py collectstatic --noinput
log_success "静态文件收集完成"

# 11. 创建新的systemd服务文件（支持ASGI）
log_info "🔧 创建ASGI服务文件..."
sudo tee /etc/systemd/system/badminton-analysis.service > /dev/null <<EOF
[Unit]
Description=Badminton Analysis Django Application (WebSocket)
After=network.target redis-server.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
Environment=DJANGO_SETTINGS_MODULE=djangodemo.settings
ExecStart=$(pwd)/venv/bin/daphne -b 0.0.0.0 -p 8000 djangodemo.asgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 12. 创建新的Nginx配置（支持WebSocket）
log_info "🌐 配置Nginx支持WebSocket..."
sudo tee /etc/nginx/sites-available/badminton-analysis > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    # 客户端最大上传大小
    client_max_body_size 100M;
    
    # 静态文件
    location /static/ {
        alias $(pwd)/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 媒体文件
    location /images/ {
        alias $(pwd)/images/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # WebSocket支持
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }
    
    # HTTP代理
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
EOF

# 启用Nginx配置
sudo ln -sf /etc/nginx/sites-available/badminton-analysis /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 测试Nginx配置
sudo nginx -t
sudo systemctl restart nginx

log_success "Nginx配置完成"

# 13. 启动服务
log_info "🚀 启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable badminton-analysis.service
sudo systemctl start badminton-analysis.service

# 14. 等待服务启动
log_info "⏳ 等待服务启动..."
sleep 10

# 15. 检查服务状态
log_info "✅ 检查服务状态..."
if sudo systemctl is-active --quiet badminton-analysis.service; then
    log_success "服务启动成功"
else
    log_error "服务启动失败"
    sudo systemctl status badminton-analysis.service --no-pager
    exit 1
fi

# 16. 检查WebSocket连接
log_info "🔌 测试WebSocket连接..."
curl -s http://localhost:8000/ > /dev/null && log_success "HTTP服务正常" || log_error "HTTP服务异常"

# 17. 显示部署信息
echo ""
echo "🎉 WebSocket版本部署完成！"
echo "================================================"
echo "📊 服务地址: http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):8000"
echo "🔧 管理地址: http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):8000/admin"
echo "🔌 WebSocket端点: ws://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):8000/ws/"
echo ""
echo "📝 常用命令:"
echo "  查看日志: sudo journalctl -u badminton-analysis.service -f"
echo "  停止服务: sudo systemctl stop badminton-analysis.service"
echo "  启动服务: sudo systemctl start badminton-analysis.service"
echo "  重启服务: sudo systemctl restart badminton-analysis.service"
echo "  重启Nginx: sudo systemctl restart nginx"
echo ""
echo "🔍 测试WebSocket连接:"
echo "  ESP32设备: ws://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):8000/ws/esp32/{device_code}/"
echo "  小程序: ws://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):8000/ws/miniprogram/{user_id}/"
echo "  管理后台: ws://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):8000/ws/admin/"
echo ""
echo "📦 备份位置: $BACKUP_DIR"
echo "================================================" 