#!/bin/bash

# 羽毛球分析系统 - 服务器快速更新脚本
# 使用方法: chmod +x quick_server_update.sh && ./quick_server_update.sh

echo "🚀 羽毛球分析系统 - 服务器更新脚本"
echo "==============================================="
echo "开始时间: $(date)"
echo ""

# 配置变量（根据实际情况修改）
PROJECT_DIR="/var/www/badminton-analysis"
BACKUP_DIR="/var/www/backups"
PYTHON_CMD="python"
SERVICE_NAME="badminton-analysis"

# 检查是否为root用户或有sudo权限
if [[ $EUID -eq 0 ]]; then
    SUDO=""
else
    SUDO="sudo"
fi

# 函数：打印状态
print_status() {
    echo "📋 $1"
}

print_success() {
    echo "✅ $1"
}

print_error() {
    echo "❌ $1"
}

print_warning() {
    echo "⚠️ $1"
}

# 函数：检查命令是否成功
check_success() {
    if [ $? -eq 0 ]; then
        print_success "$1"
    else
        print_error "$1 失败！"
        exit 1
    fi
}

# 第1步：检查当前环境
print_status "步骤1: 检查当前环境"

if [ ! -d "$PROJECT_DIR" ]; then
    print_error "项目目录不存在: $PROJECT_DIR"
    exit 1
fi

cd $PROJECT_DIR
print_success "切换到项目目录: $PROJECT_DIR"

# 检查Git仓库
if [ ! -d ".git" ]; then
    print_error "这不是一个Git仓库！"
    exit 1
fi

# 第2步：停止当前服务
print_status "步骤2: 停止当前服务"

# 查找Daphne进程
DAPHNE_PID=$(pgrep -f "daphne.*djangodemo.asgi")
if [ ! -z "$DAPHNE_PID" ]; then
    print_status "找到Daphne进程: $DAPHNE_PID"
    kill $DAPHNE_PID
    sleep 2
    # 强制杀死如果还在运行
    if pgrep -f "daphne.*djangodemo.asgi" > /dev/null; then
        pkill -9 -f "daphne.*djangodemo.asgi"
    fi
    print_success "Daphne服务已停止"
else
    print_warning "未找到运行中的Daphne进程"
fi

# 第3步：备份当前代码
print_status "步骤3: 备份当前代码"

mkdir -p $BACKUP_DIR
BACKUP_NAME="badminton-analysis-backup-$(date +%Y%m%d-%H%M%S)"
cp -r $PROJECT_DIR $BACKUP_DIR/$BACKUP_NAME
check_success "代码备份到: $BACKUP_DIR/$BACKUP_NAME"

# 第4步：更新代码
print_status "步骤4: 更新代码"

echo "当前分支和提交:"
git branch
git log --oneline -3

echo ""
print_status "拉取最新代码..."
git fetch origin
git pull origin master
check_success "Git代码更新"

echo "更新后的提交:"
git log --oneline -3

# 第5步：检查Python环境
print_status "步骤5: 检查Python环境"

# 尝试激活虚拟环境
if [ -d "venv/bin" ]; then
    source venv/bin/activate
    print_success "虚拟环境已激活"
elif [ -d "env/bin" ]; then
    source env/bin/activate
    print_success "虚拟环境已激活"
else
    print_warning "未找到虚拟环境，使用系统Python"
fi

# 检查关键依赖
$PYTHON_CMD -c "import django; print(f'Django: {django.get_version()}')"
$PYTHON_CMD -c "import matplotlib; print('matplotlib: OK')"
check_success "Python依赖检查"

# 第6步：数据库迁移
print_status "步骤6: 数据库迁移"
$PYTHON_CMD manage.py makemigrations
$PYTHON_CMD manage.py migrate
check_success "数据库迁移"

# 第7步：创建必要目录和权限
print_status "步骤7: 创建目录和设置权限"

mkdir -p images
mkdir -p staticfiles
chmod 755 images
chmod 755 staticfiles
print_success "目录创建完成"

# 收集静态文件
$PYTHON_CMD manage.py collectstatic --noinput
check_success "静态文件收集"

# 第8步：测试配置
print_status "步骤8: 测试配置"
$PYTHON_CMD manage.py check
check_success "Django配置检查"

# 测试matplotlib
$PYTHON_CMD -c "import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt; print('matplotlib图片生成测试: OK')"
check_success "matplotlib测试"

# 第9步：启动服务
print_status "步骤9: 启动服务"

# 检查端口是否被占用
if netstat -tlnp | grep :8000 > /dev/null; then
    print_warning "端口8000仍被占用，尝试清理..."
    $SUDO lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# 启动Daphne服务
nohup daphne -b 0.0.0.0 -p 8000 djangodemo.asgi:application > daphne.log 2>&1 &
sleep 3

# 检查服务是否启动成功
if pgrep -f "daphne.*djangodemo.asgi" > /dev/null; then
    print_success "Daphne服务启动成功"
    echo "进程ID: $(pgrep -f 'daphne.*djangodemo.asgi')"
else
    print_error "Daphne服务启动失败！"
    echo "查看日志:"
    tail -20 daphne.log
    exit 1
fi

# 第10步：验证部署
print_status "步骤10: 验证部署"

sleep 5  # 等待服务完全启动

# 测试基本连接
print_status "测试服务连接..."
if curl -s http://localhost:8000/ > /dev/null; then
    print_success "基本连接测试通过"
else
    print_error "基本连接测试失败"
fi

# 测试调试API
print_status "测试调试API..."
if curl -s http://localhost:8000/api/debug_images/ | grep -q "timestamp"; then
    print_success "调试API测试通过"
else
    print_warning "调试API测试失败"
fi

# 测试小程序API
print_status "测试小程序API..."
if curl -s http://localhost:8000/api/miniprogram/get_images/ > /dev/null; then
    print_success "小程序API测试通过"
else
    print_warning "小程序API测试失败"
fi

# 生成测试图片
print_status "测试图片生成..."
curl -s -X POST http://localhost:8000/api/debug_images/ -d 'action=regenerate' > /dev/null
if [ -f "images/test_analysis_curve.jpg" ]; then
    print_success "图片生成测试通过"
else
    print_warning "图片生成测试失败"
fi

# 第11步：显示状态信息
print_status "部署状态信息"
echo "==============================================="
echo "🔍 服务状态:"
echo "  进程: $(pgrep -f 'daphne.*djangodemo.asgi' | wc -l) 个Daphne进程运行中"
echo "  端口: $(netstat -tlnp | grep :8000 | wc -l) 个进程监听8000端口"
echo "  图片: $(ls images/*.jpg 2>/dev/null | wc -l) 个图片文件"

echo ""
echo "📁 目录信息:"
echo "  项目目录: $PROJECT_DIR"
echo "  备份目录: $BACKUP_DIR/$BACKUP_NAME"
echo "  图片目录: $PROJECT_DIR/images ($(ls images/ 2>/dev/null | wc -l) 个文件)"

echo ""
echo "🌐 测试URL:"
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")
echo "  主页: http://$SERVER_IP:8000/"
echo "  调试API: http://$SERVER_IP:8000/api/debug_images/"
echo "  小程序API: http://$SERVER_IP:8000/api/miniprogram/get_images/"
echo "  图片访问: http://$SERVER_IP:8000/images/test_analysis_curve.jpg"

echo ""
echo "📋 有用的命令:"
echo "  查看日志: tail -f $PROJECT_DIR/daphne.log"
echo "  重启服务: pkill -f daphne && cd $PROJECT_DIR && nohup daphne -b 0.0.0.0 -p 8000 djangodemo.asgi:application > daphne.log 2>&1 &"
echo "  查看进程: ps aux | grep daphne"
echo "  测试API: curl http://localhost:8000/api/debug_images/"

echo ""
print_success "部署更新完成！"
echo "完成时间: $(date)"
echo "==============================================="

# 最后提示
echo ""
echo "🎯 下一步:"
echo "1. 在浏览器中访问 http://$SERVER_IP:8000/ 验证服务"
echo "2. 使用小程序测试图片获取API"
echo "3. 查看日志确认没有错误: tail -f daphne.log" 