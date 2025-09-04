#!/bin/bash

# 羽毛球分析系统 - 服务器端图片调试脚本
# 适用于CentOS服务器

echo "🔍 羽毛球分析系统 - 图片调试脚本"
echo "执行时间: $(date)"
echo "========================================"

# 1. 检查项目目录和权限
echo -e "\n📁 检查项目目录..."
PROJECT_DIR="/var/www/badminton-analysis"
if [ -d "$PROJECT_DIR" ]; then
    echo "✅ 项目目录存在: $PROJECT_DIR"
    echo "   权限: $(ls -ld $PROJECT_DIR | awk '{print $1}')"
    echo "   所有者: $(ls -ld $PROJECT_DIR | awk '{print $3":"$4}')"
else
    echo "❌ 项目目录不存在: $PROJECT_DIR"
fi

# 2. 检查images目录
echo -e "\n📁 检查images目录..."
IMAGES_DIR="$PROJECT_DIR/images"
if [ -d "$IMAGES_DIR" ]; then
    echo "✅ images目录存在: $IMAGES_DIR"
    echo "   权限: $(ls -ld $IMAGES_DIR | awk '{print $1}')"
    echo "   所有者: $(ls -ld $IMAGES_DIR | awk '{print $3":"$4}')"
    echo "   文件数量: $(ls -1 $IMAGES_DIR | wc -l)"
    echo "   图片文件:"
    ls -la $IMAGES_DIR/*.jpg $IMAGES_DIR/*.png 2>/dev/null || echo "   无图片文件"
else
    echo "❌ images目录不存在，正在创建..."
    mkdir -p $IMAGES_DIR
    chmod 755 $IMAGES_DIR
    echo "✅ images目录已创建: $IMAGES_DIR"
fi

# 3. 检查Django进程
echo -e "\n🔍 检查Django进程..."
DJANGO_PROCESS=$(ps aux | grep -E "(python.*manage.py|gunicorn.*djangodemo)" | grep -v grep)
if [ -n "$DJANGO_PROCESS" ]; then
    echo "✅ Django进程运行中:"
    echo "$DJANGO_PROCESS"
else
    echo "❌ Django进程未运行"
fi

# 4. 检查Nginx进程
echo -e "\n🔍 检查Nginx进程..."
NGINX_PROCESS=$(ps aux | grep nginx | grep -v grep)
if [ -n "$NGINX_PROCESS" ]; then
    echo "✅ Nginx进程运行中:"
    echo "$NGINX_PROCESS"
else
    echo "❌ Nginx进程未运行"
fi

# 5. 检查端口占用
echo -e "\n🔍 检查端口占用..."
echo "端口8000 (Django):"
netstat -tlnp | grep :8000 || echo "   端口8000未监听"
echo "端口80 (Nginx):"
netstat -tlnp | grep :80 || echo "   端口80未监听"

# 6. 测试图片API
echo -e "\n📡 测试图片相关API..."
API_BASE="http://localhost:8000/api"

# 测试调试API
echo "测试 debug_images API:"
curl -s -w "HTTP状态码: %{http_code}\n" -o /tmp/debug_response.json "$API_BASE/debug_images/" || echo "请求失败"

if [ -f "/tmp/debug_response.json" ]; then
    echo "响应内容 (前200字符):"
    head -c 200 /tmp/debug_response.json
    echo -e "\n..."
fi

# 测试图片列表API
echo -e "\n测试 list_images API:"
curl -s -w "HTTP状态码: %{http_code}\n" -o /tmp/images_response.json "$API_BASE/list_images/" || echo "请求失败"

# 7. 检查Nginx配置
echo -e "\n🔍 检查Nginx配置..."
NGINX_CONF="/etc/nginx/nginx.conf"
SITES_AVAILABLE="/etc/nginx/sites-available"
SITES_ENABLED="/etc/nginx/sites-enabled"

if [ -f "$NGINX_CONF" ]; then
    echo "✅ 主配置文件存在: $NGINX_CONF"
else
    echo "❌ 主配置文件不存在: $NGINX_CONF"
fi

if [ -d "$SITES_AVAILABLE" ]; then
    echo "✅ sites-available目录存在"
    echo "   配置文件:"
    ls -la $SITES_AVAILABLE/
else
    echo "❌ sites-available目录不存在"
fi

# 8. 检查防火墙状态
echo -e "\n🔍 检查防火墙状态..."
if command -v firewall-cmd &> /dev/null; then
    echo "FirewallD状态:"
    firewall-cmd --state 2>/dev/null || echo "FirewallD未运行"
    echo "开放端口:"
    firewall-cmd --list-ports 2>/dev/null || echo "无法获取端口信息"
elif command -v iptables &> /dev/null; then
    echo "iptables规则:"
    iptables -L -n | head -10
fi

# 9. 生成测试图片URL
echo -e "\n🔗 图片访问URL测试..."
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")
echo "可能的图片访问URL:"
echo "  http://$SERVER_IP/images/latest_multi_sensor_curve.jpg"
echo "  http://$SERVER_IP/images/test_analysis_curve.jpg"
echo "  http://$SERVER_IP/images/debug_test_image.jpg"

# 10. 提供解决建议
echo -e "\n🎯 调试建议:"
echo "========================================"
echo "1. 确保images目录权限正确: chmod 755 $IMAGES_DIR"
echo "2. 确保Django进程运行: sudo systemctl status your-django-service"
echo "3. 确保Nginx配置包含静态文件处理"
echo "4. 检查防火墙开放80和8000端口"
echo "5. 测试API调用: curl http://localhost:8000/api/debug_images/"
echo "6. 检查Django日志: tail -f /path/to/django.log"
echo "7. 检查Nginx日志: tail -f /var/log/nginx/error.log"

# 11. 生成快速修复命令
echo -e "\n⚡ 快速修复命令:"
echo "========================================"
echo "# 创建并设置images目录权限"
echo "sudo mkdir -p $IMAGES_DIR"
echo "sudo chmod 755 $IMAGES_DIR"
echo "sudo chown www-data:www-data $IMAGES_DIR"
echo ""
echo "# 重启服务"
echo "sudo systemctl restart nginx"
echo "sudo systemctl restart your-django-service"
echo ""
echo "# 测试图片生成"
echo "curl -X POST http://localhost:8000/api/debug_images/ -d 'action=regenerate'"

echo -e "\n✅ 调试脚本执行完成: $(date)" 