#!/bin/bash
# UDP广播抓包脚本

echo "📡 开始抓取UDP广播包 (端口: 8888)..."
echo "按 Ctrl+C 停止抓包"
echo "=================================="

# 抓取UDP端口8888的广播包
tcpdump -i any -n udp port 8888 -A 