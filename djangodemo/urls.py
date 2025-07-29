"""
URL configuration for djangodemo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from wxapp.admin import custom_admin_site
from wxapp import views as wxapp_views
from django.conf import settings
from django.conf.urls.static import static

def index(request):
    return HttpResponse("""
    <h1>羽毛球动作分析系统</h1>
    <p>系统运行正常！</p>
    <ul>
        <li><a href="/admin/">管理后台</a></li>
        <li><a href="/admin/upload_mat/">上传.mat文件</a></li>
        <li>微信小程序接口: /wxapp/</li>
        <li>数据采集接口: /wxapp/start_session/</li>
        <li>分析结果接口: /wxapp/get_analysis/</li>
    </ul>
    <p><strong>系统功能：</strong></p>
    <ul>
        <li>微信用户管理</li>
        <li>设备绑定管理</li>
        <li>数据采集会话</li>
        <li>传感器数据存储</li>
        <li>动作分析算法</li>
        <li>分析结果可视化</li>
    </ul>
    """)

urlpatterns = [
    path('', index),  # 添加首页
    path('admin/', custom_admin_site.urls),
    path('wxapp/', include('wxapp.urls')),
    path('wxapp/latest_analysis_images/', wxapp_views.latest_analysis_images, name='latest_analysis_images'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
