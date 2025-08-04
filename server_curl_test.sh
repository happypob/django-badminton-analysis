#!/bin/bash

# 服务器端curl测试脚本
echo "🚀 开始服务器端采集测试..."

SERVER_URL="http://47.122.129.159:8000"

echo "📡 测试1: UDP广播测试"
curl -X POST $SERVER_URL/wxapp/test_udp_broadcast/ \
  -d "message=Hello ESP32 from server!" \
  -d "device_code=2025001"
echo -e "\n"

echo "📡 测试2: 创建会话"
SESSION_RESPONSE=$(curl -s -X POST $SERVER_URL/wxapp/start_session/ \
  -d "openid=test_user_123456" \
  -d "device_group_code=2025001")
echo $SESSION_RESPONSE
echo -e "\n"

# 提取会话ID
SESSION_ID=$(echo $SESSION_RESPONSE | grep -o '"session_id":[0-9]*' | cut -d':' -f2)
echo "📋 会话ID: $SESSION_ID"

echo "📡 测试3: 开始数据采集"
curl -X POST $SERVER_URL/wxapp/start_data_collection/ \
  -d "session_id=$SESSION_ID" \
  -d "device_code=2025001"
echo -e "\n"

echo "📡 测试4: 结束采集"
curl -X POST $SERVER_URL/wxapp/end_session/ \
  -d "session_id=$SESSION_ID" \
  -d "device_code=2025001"
echo -e "\n"

echo "🎉 服务器端测试完成!"
echo "📡 UDP广播端口: 8888"
echo "🌐 服务器地址: $SERVER_URL" 