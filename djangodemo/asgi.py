"""
ASGI config for djangodemo project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application

# 必须在导入任何Django模型之前设置环境变量并初始化Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangodemo.settings')
django.setup()

# 现在可以安全地导入channels和routing
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import wxapp.routing

# 获取Django的ASGI应用
django_asgi_app = get_asgi_application()

# 配置ASGI应用以支持HTTP和WebSocket
application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            wxapp.routing.websocket_urlpatterns
        )
    ),
})
