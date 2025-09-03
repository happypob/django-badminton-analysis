"""
WebSocket路由配置
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # ESP32设备WebSocket连接
    re_path(r'ws/esp32/(?P<device_code>\w+)/$', consumers.ESP32Consumer.as_asgi()),
    # 小程序WebSocket连接
    re_path(r'ws/miniprogram/(?P<user_id>\w+)/$', consumers.MiniProgramConsumer.as_asgi()),
    # 管理后台WebSocket连接
    re_path(r'ws/admin/$', consumers.AdminConsumer.as_asgi()),
] 