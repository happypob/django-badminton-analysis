#!/bin/bash

# 羽毛球动作分析系统部署脚本
# 适用于Linux服务器

set -e

echo "🚀 开始部署羽毛球动作分析系统..."

# 检查Python版本
python3 --version

# 创建虚拟环境
echo "📦 创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装依赖
echo "📥 安装项目依赖..."
pip install -r requirements.txt
pip install gunicorn

# 收集静态文件
echo "📁 收集静态文件..."
python manage.py collectstatic --noinput

# 数据库迁移
echo "🗄️ 运行数据库迁移..."
python manage.py makemigrations
python manage.py migrate

# 创建超级用户 (如果需要)
echo "👤 创建管理员用户..."
python create_admin.py

# 设置权限
echo "🔐 设置文件权限..."
chmod +x gunicorn.conf.py

echo "✅ 部署完成!"
echo "🌐 启动服务器: gunicorn -c gunicorn.conf.py djangodemo.wsgi:application"
echo "📊 管理后台: http://your-domain.com/admin/" 