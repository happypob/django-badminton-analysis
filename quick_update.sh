#!/bin/bash

# 快速更新脚本 - 服务器端使用

echo "🔄 开始更新羽毛球分析系统..."

# 1. 进入项目目录
cd /opt/badminton-analysis

# 2. 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin master

# 3. 激活虚拟环境
echo "🐍 激活虚拟环境..."
source venv38/bin/activate

# 4. 安装/更新依赖
echo "📚 更新Python依赖..."
pip install numpy scipy matplotlib pandas django djangorestframework

# 5. 执行数据库迁移
echo "🗄️ 执行数据库迁移..."
python manage.py makemigrations
python manage.py migrate

# 6. 收集静态文件
echo "📦 收集静态文件..."
python manage.py collectstatic --noinput

# 7. 停止现有服务
echo "🛑 停止现有服务..."
pkill -f "python manage.py runserver" || true
pkill -f "gunicorn" || true

# 8. 启动服务
echo "🚀 启动服务..."
nohup python manage.py runserver 0.0.0.0:8000 > server.log 2>&1 &

# 9. 检查服务状态
echo "✅ 检查服务状态..."
sleep 3
ps aux | grep "python manage.py runserver" | grep -v grep

echo "🎉 更新完成！"
echo "📊 服务地址: http://$(curl -s ifconfig.me):8000"
echo "📝 查看日志: tail -f server.log"
echo "🛑 停止服务: pkill -f 'python manage.py runserver'" 