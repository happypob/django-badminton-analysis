#!/bin/bash

# 服务器端更新脚本
echo "🚀 开始更新服务器代码..."

# 进入项目目录
cd /opt/badminton-analysis

# 停止当前运行的Django服务器
echo "📋 停止当前Django服务器..."
pkill -f "python manage.py runserver"

# 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin master

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv38/bin/activate

# 安装/更新依赖
echo "📦 更新依赖..."
pip install -r requirements.txt

# 执行数据库迁移（如果需要）
echo "🗄️ 执行数据库迁移..."
python manage.py migrate

# 收集静态文件（如果需要）
echo "📁 收集静态文件..."
python manage.py collectstatic --noinput

# 启动Django服务器
echo "🚀 启动Django服务器..."
nohup python manage.py runserver 0.0.0.0:8000 > django.log 2>&1 &

# 等待服务器启动
sleep 3

# 检查服务器状态
echo "🔍 检查服务器状态..."
if curl -s http://localhost:8000/wxapp/test_udp_broadcast/ > /dev/null; then
    echo "✅ 服务器启动成功!"
    echo "🌐 服务器地址: http://47.122.129.159:8000"
    echo "📡 UDP广播端口: 8888"
else
    echo "❌ 服务器启动失败，请检查日志"
    tail -n 20 django.log
fi

echo "🎉 更新完成!" 