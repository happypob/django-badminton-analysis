"""
URL configuration for djangodemo project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

def home_view(request):
    return HttpResponse("""
    <html>
    <head>
        <title>羽毛球动作分析系统</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>羽毛球动作分析系统</h1>
        <p>系统已成功部署！</p>
        <ul>
            <li><a href="/admin/">管理后台</a></li>
            <li><a href="/api/">API接口</a></li>
            <li><a href="/api/debug_images/">图片调试</a></li>
            <li><a href="/api/list_images/">图片列表</a></li>
        </ul>
    </body>
    </html>
    """)

def websocket_test_view(request):
    from django.shortcuts import render
    return render(request, 'websocket_test.html')

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('wxapp.urls')),
    path('wxapp/', include('wxapp.urls')),  # 添加wxapp前缀
    path('websocket-test/', websocket_test_view, name='websocket_test'),  # WebSocket测试页面
]

# 静态文件和媒体文件处理 - 适用于Daphne部署
# 在生产环境中也需要处理MEDIA文件，因为你使用的是Daphne而不是Nginx
if settings.DEBUG:
    # 开发环境
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # 生产环境 - Daphne需要这些配置来处理静态文件
    from django.views.static import serve
    from django.urls import re_path
    
    # 添加MEDIA文件处理
    urlpatterns += [
        re_path(r'^images/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
        re_path(r'^static/(?P<path>.*)$', serve, {
            'document_root': settings.STATIC_ROOT,
        }),
    ]
