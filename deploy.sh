#!/bin/bash

# 羽毛球动作分析系统部署脚本
# 适用于Linux服务器

set -e

echo "🚀 开始部署羽毛球动作分析系统..."

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
    echo "❌ 请不要使用root用户运行此脚本"
    exit 1
fi

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

python3 --version

# 检查Docker是否安装
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "🐳 检测到Docker环境，使用Docker部署..."
    
    # 创建环境变量文件
    if [ ! -f .env ]; then
        echo "📝 创建环境变量文件..."
        cp .env.example .env
        echo "⚠️  请编辑 .env 文件配置您的环境变量"
    fi
    
    # 构建并启动服务
    echo "🔨 构建Docker镜像..."
    docker-compose -f docker-compose.prod.yml build
    
    echo "🚀 启动服务..."
    docker-compose -f docker-compose.prod.yml up -d
    
    echo "✅ Docker部署完成!"
    echo "🌐 服务地址: http://localhost"
    echo "📊 管理后台: http://localhost/admin/"
    echo "📈 监控面板: http://localhost:3000"
    
else
    echo "🐍 使用传统方式部署..."
    
    # 创建虚拟环境
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    echo "📥 安装项目依赖..."
    pip install -r requirements.txt
    
    # 创建必要目录
    echo "📁 创建必要目录..."
    mkdir -p images logs staticfiles
    
    # 收集静态文件
    echo "📁 收集静态文件..."
    python manage.py collectstatic --noinput
    
    # 数据库迁移
    echo "🗄️ 运行数据库迁移..."
    python manage.py makemigrations
    python manage.py migrate
    
    # 创建超级用户
    echo "👤 创建管理员用户..."
    python manage.py createsuperuser --noinput --username admin --email admin@example.com || echo "管理员用户已存在"
    
    # 设置权限
    echo "🔐 设置文件权限..."
    chmod 755 images logs staticfiles
    
    echo "✅ 传统部署完成!"
    echo "🌐 启动服务器: python manage.py runserver 0.0.0.0:8000"
    echo "🌐 启动WebSocket: daphne -b 0.0.0.0 -p 8001 djangodemo.asgi:application"
    echo "📊 管理后台: http://localhost:8000/admin/"
fi

echo ""
echo "🎯 下一步:"
echo "1. 配置环境变量 (.env 文件)"
echo "2. 配置域名和SSL证书"
echo "3. 设置防火墙规则"
echo "4. 配置监控和日志"
echo "5. 测试所有功能" 