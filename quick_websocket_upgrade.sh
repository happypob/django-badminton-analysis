#!/bin/bash

# 羽毛球分析系统 - WebSocket快速升级脚本
# 适用于从GitHub仓库升级到WebSocket版本

set -e

echo "🚀 开始快速升级到WebSocket版本..."
echo "================================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 1. 检查Git仓库
if [ ! -d ".git" ]; then
    log_error "当前目录不是Git仓库，请先克隆项目"
    exit 1
fi

# 2. 备份当前状态
log_info "📦 备份当前状态..."
git stash push -m "Backup before WebSocket upgrade $(date)"
log_success "当前状态已备份"

# 3. 拉取最新代码
log_info "📥 拉取最新代码..."
git pull origin master
log_success "代码更新完成"

# 4. 停止现有服务
log_info "🛑 停止现有服务..."
sudo systemctl stop badminton-analysis.service 2>/dev/null || true
sudo pkill -f "python manage.py runserver" 2>/dev/null || true
sudo pkill -f "gunicorn" 2>/dev/null || true
sudo pkill -f "daphne" 2>/dev/null || true

# 5. 安装Redis（如果未安装）
if ! systemctl is-active --quiet redis-server; then
    log_info "🔴 安装并启动Redis..."
    sudo apt update
    sudo apt install -y redis-server
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
    log_success "Redis安装完成"
else
    log_success "Redis已运行"
fi

# 6. 更新Python依赖
log_info "🐍 更新Python依赖..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install channels[redis] daphne
log_success "Python依赖更新完成"

# 7. 数据库迁移
log_info "🗄️ 执行数据库迁移..."
python manage.py makemigrations
python manage.py migrate
log_success "数据库迁移完成"

# 8. 收集静态文件
log_info "📦 收集静态文件..."
python manage.py collectstatic --noinput
log_success "静态文件收集完成"

# 9. 更新systemd服务文件
log_info "🔧 更新服务配置..."
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

# 10. 更新Nginx配置
log_info "🌐 更新Nginx配置..."
sudo tee /etc/nginx/sites-available/badminton-analysis > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    client_max_body_size 100M;
    
    location /static/ {
        alias $(pwd)/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /images/ {
        alias $(pwd)/images/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
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
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
EOF

sudo nginx -t
sudo systemctl restart nginx
log_success "Nginx配置更新完成"

# 11. 重启服务
log_info "🚀 重启服务..."
sudo systemctl daemon-reload
sudo systemctl enable badminton-analysis.service
sudo systemctl start badminton-analysis.service

# 12. 等待服务启动
log_info "⏳ 等待服务启动..."
sleep 10

# 13. 检查服务状态
if sudo systemctl is-active --quiet badminton-analysis.service; then
    log_success "服务启动成功"
else
    log_error "服务启动失败"
    sudo systemctl status badminton-analysis.service --no-pager
    exit 1
fi

# 14. 显示升级结果
echo ""
echo "🎉 WebSocket版本升级完成！"
echo "================================================"
echo "📊 服务地址: http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):8000"
echo "🔧 管理地址: http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):8000/admin"
echo "🔌 WebSocket端点: ws://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):8000/ws/"
echo ""
echo "📝 常用命令:"
echo "  查看日志: sudo journalctl -u badminton-analysis.service -f"
echo "  重启服务: sudo systemctl restart badminton-analysis.service"
echo "  重启Nginx: sudo systemctl restart nginx"
echo ""
echo "🔍 WebSocket连接测试:"
echo "  ESP32设备: ws://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):8000/ws/esp32/{device_code}/"
echo "  小程序: ws://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):8000/ws/miniprogram/{user_id}/"
echo "  管理后台: ws://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):8000/ws/admin/"
echo ""
echo "📦 如需回滚: git stash pop"
echo "================================================" 