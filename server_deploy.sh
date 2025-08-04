#!/bin/bash

# 羽毛球分析系统 - 服务器部署脚本
# 适用于阿里云/腾讯云等Linux服务器

echo "🚀 开始部署羽毛球分析系统..."

# 1. 更新系统包
echo "📦 更新系统包..."
sudo apt update
sudo apt upgrade -y

# 2. 安装必要的系统依赖
echo "🔧 安装系统依赖..."
sudo apt install -y python3 python3-pip python3-venv git nginx supervisor

# 3. 创建项目目录
echo "📁 创建项目目录..."
sudo mkdir -p /opt/badminton-analysis
sudo chown $USER:$USER /opt/badminton-analysis
cd /opt/badminton-analysis

# 4. 克隆项目（如果还没有）
if [ ! -d ".git" ]; then
    echo "📥 克隆项目代码..."
    git clone https://github.com/your-username/djangodemo.git .
else
    echo "📥 更新项目代码..."
    git pull origin master
fi

# 5. 创建虚拟环境
echo "🐍 创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 6. 安装Python依赖
echo "📚 安装Python依赖..."
pip install --upgrade pip
pip install -r requirements.txt
pip install numpy scipy matplotlib pandas django djangorestframework

# 7. 配置Django设置
echo "⚙️ 配置Django设置..."
python manage.py makemigrations
python manage.py migrate

# 8. 创建超级用户（如果需要）
echo "👤 创建管理员用户..."
python manage.py createsuperuser --noinput --username admin --email admin@example.com || echo "管理员用户已存在"

# 9. 收集静态文件
echo "📦 收集静态文件..."
python manage.py collectstatic --noinput

# 10. 停止现有服务
echo "🛑 停止现有服务..."
sudo pkill -f "python manage.py runserver" || true
sudo pkill -f "gunicorn" || true

# 11. 创建systemd服务文件
echo "🔧 创建systemd服务..."
sudo tee /etc/systemd/system/badminton-analysis.service > /dev/null <<EOF
[Unit]
Description=Badminton Analysis Django Application
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=/opt/badminton-analysis
Environment=PATH=/opt/badminton-analysis/venv/bin
ExecStart=/opt/badminton-analysis/venv/bin/python manage.py runserver 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 12. 重新加载systemd并启动服务
echo "🚀 启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable badminton-analysis.service
sudo systemctl start badminton-analysis.service

# 13. 配置Nginx（可选）
echo "🌐 配置Nginx..."
sudo tee /etc/nginx/sites-available/badminton-analysis > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias /opt/badminton-analysis/static/;
    }
}
EOF

# 启用Nginx配置
sudo ln -sf /etc/nginx/sites-available/badminton-analysis /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

# 14. 配置防火墙
echo "🔥 配置防火墙..."
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 8000
sudo ufw --force enable

# 15. 检查服务状态
echo "✅ 检查服务状态..."
sleep 5
sudo systemctl status badminton-analysis.service --no-pager

echo "🎉 部署完成！"
echo "📊 服务地址: http://$(curl -s ifconfig.me):8000"
echo "🔧 管理地址: http://$(curl -s ifconfig.me):8000/admin"
echo "📝 日志查看: sudo journalctl -u badminton-analysis.service -f"
echo "🛑 停止服务: sudo systemctl stop badminton-analysis.service"
echo "🚀 启动服务: sudo systemctl start badminton-analysis.service"
echo "🔄 重启服务: sudo systemctl restart badminton-analysis.service" 