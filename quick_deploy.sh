#!/bin/bash

# 阿里云服务器快速部署脚本
# 羽毛球动作分析系统

set -e

echo "🚀 开始快速部署羽毛球动作分析系统..."

# 更新系统
echo "📦 更新系统包..."
apt update && apt upgrade -y

# 安装必要工具
echo "🔧 安装必要工具..."
apt install -y curl wget git unzip

# 安装Docker
echo "🐳 安装Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 安装Docker Compose
echo "📦 安装Docker Compose..."
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 启动Docker服务
systemctl start docker
systemctl enable docker

# 创建项目目录
echo "📁 创建项目目录..."
mkdir -p /opt/badminton-analysis
cd /opt/badminton-analysis

# 创建环境变量文件
echo "🔐 创建环境变量..."
cat > .env << EOF
DEBUG=False
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
DB_NAME=badminton_db
DB_USER=postgres
DB_PASSWORD=badminton123456
DB_HOST=db
DB_PORT=5432
EOF

echo "✅ Docker环境准备完成!"
echo "📋 下一步：上传项目文件到服务器"
echo "🌐 项目将部署在: http://your-server-ip" 