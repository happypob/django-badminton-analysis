#!/bin/bash
# 服务器端UDP广播监听脚本

echo "🔍 服务器端UDP广播监听"
echo "=========================="

# 检查是否在服务器环境
if [ -f "/etc/redhat-release" ] || [ -f "/etc/debian_version" ]; then
    echo "✅ 检测到Linux服务器环境"
    
    # 检查netcat是否安装
    if command -v nc &> /dev/null; then
        echo "✅ netcat已安装，使用netcat监听"
        echo "📡 开始监听UDP端口8888..."
        echo "按 Ctrl+C 停止监听"
        echo "=========================="
        nc -ul 8888
    else
        echo "❌ netcat未安装，尝试使用tcpdump"
        if command -v tcpdump &> /dev/null; then
            echo "✅ tcpdump已安装，使用tcpdump抓包"
            echo "📡 开始抓取UDP端口8888的广播包..."
            echo "按 Ctrl+C 停止抓包"
            echo "=========================="
            tcpdump -i any -n udp port 8888 -A
        else
            echo "❌ 未找到合适的监听工具"
            echo "请安装netcat或tcpdump:"
            echo "  CentOS/RHEL: yum install nc tcpdump"
            echo "  Ubuntu/Debian: apt-get install netcat tcpdump"
        fi
    fi
else
    echo "❌ 未检测到Linux服务器环境"
    echo "请在Linux服务器上运行此脚本"
fi 