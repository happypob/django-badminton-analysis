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
        </ul>
    </body>
    </html>
    """)

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('wxapp.urls')),
    path('wxapp/', include('wxapp.urls')),  # 添加wxapp前缀
]

# 开发环境静态文件处理
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
