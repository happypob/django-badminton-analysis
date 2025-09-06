from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.utils.html import format_html
from django.db import models
from .models import WxUser, DeviceBind, SensorData, DeviceGroup, DataCollectionSession, AnalysisResult
from .views import process_mat_data, generate_detailed_report
from scipy.io import loadmat
import tempfile
import os
import json

# 自定义Admin配置
@admin.register(WxUser)
class WxUserAdmin(admin.ModelAdmin):
    list_display = ('openid', 'user', 'get_user_info')
    search_fields = ('openid', 'user__username')
    list_filter = ('user__is_active',)
    
    def get_user_info(self, obj):
        if obj.user:
            return f"用户ID: {obj.user.id}"
        return "未关联Django用户"
    get_user_info.short_description = '用户信息'

@admin.register(DeviceBind)
class DeviceBindAdmin(admin.ModelAdmin):
    list_display = ('wx_user', 'device_code', 'bind_time')
    list_filter = ('bind_time',)
    search_fields = ('device_code', 'wx_user__openid')

@admin.register(DeviceGroup)
class DeviceGroupAdmin(admin.ModelAdmin):
    list_display = ('group_code', 'created_time')
    search_fields = ('group_code',)
    list_filter = ('created_time',)

@admin.register(DataCollectionSession)
class DataCollectionSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'device_group', 'start_time', 'end_time', 'status', 'analysis_status', 'view_analysis_image')
    list_filter = ('status', 'start_time', 'device_group')
    search_fields = ('user__openid', 'device_group__group_code')
    readonly_fields = ('start_time', 'analysis_time')
    
    def analysis_time(self, obj):
        try:
            return obj.analysisresult.analysis_time
        except:
            return "未分析"
    analysis_time.short_description = '分析时间'
    
    def analysis_status(self, obj):
        """分析状态"""
        try:
            analysis_result = obj.analysisresult
            if analysis_result.has_image():
                return format_html('<span style="color: green;">✅ 已分析 (有图片)</span>')
            else:
                return format_html('<span style="color: orange;">⚠️ 已分析 (无图片)</span>')
        except:
            return format_html('<span style="color: red;">❌ 未分析</span>')
    analysis_status.short_description = '分析状态'
    
    def view_analysis_image(self, obj):
        """查看分析图片"""
        try:
            analysis_result = obj.analysisresult
            if analysis_result.has_image():
                image_url = analysis_result.get_image_url()
                return format_html(
                    '<a href="{}" target="_blank" style="background: #28a745; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; font-size: 12px;">查看图片</a>',
                    image_url
                )
            else:
                return format_html('<span style="color: #666; font-size: 12px;">无图片</span>')
        except:
            return format_html('<span style="color: #666; font-size: 12px;">未分析</span>')
    view_analysis_image.short_description = '分析图片'

@admin.register(SensorData)
class SensorDataAdmin(admin.ModelAdmin):
    list_display = ('sensor_type', 'device_code', 'session', 'timestamp')
    list_filter = ('sensor_type', 'timestamp', 'session')
    search_fields = ('device_code', 'session__id')
    readonly_fields = ('timestamp',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session')

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('session', 'energy_ratio', 'analysis_time', 'has_image_display', 'view_image_link')
    list_filter = ('analysis_time', 'image_generated_time')
    readonly_fields = ('analysis_time', 'image_generated_time', 'image_preview')
    fields = ('session', 'phase_delay', 'energy_ratio', 'rom_data', 'analysis_time', 'analysis_image', 'image_generated_time', 'image_preview')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session')
    
    def has_image_display(self, obj):
        """显示是否有图片"""
        if obj.has_image():
            return format_html('<span style="color: green;">✅ 有图片</span>')
        else:
            return format_html('<span style="color: red;">❌ 无图片</span>')
    has_image_display.short_description = '图片状态'
    
    def view_image_link(self, obj):
        """查看图片链接"""
        if obj.has_image():
            image_url = obj.get_image_url()
            return format_html(
                '<a href="{}" target="_blank" style="background: #007cba; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">查看图片</a>',
                image_url
            )
        else:
            return format_html('<span style="color: #666;">无图片</span>')
    view_image_link.short_description = '查看图片'
    
    def image_preview(self, obj):
        """图片预览"""
        if obj.has_image():
            image_url = obj.get_image_url()
            return format_html(
                '<div style="text-align: center;">'
                '<img src="{}" style="max-width: 600px; max-height: 400px; border: 1px solid #ddd; border-radius: 4px;">'
                '<br><small>图片路径: {}</small>'
                '<br><small>生成时间: {}</small>'
                '</div>',
                image_url,
                obj.analysis_image,
                obj.image_generated_time.strftime('%Y-%m-%d %H:%M:%S') if obj.image_generated_time else '未知'
            )
        else:
            return format_html('<p style="color: #666; text-align: center;">暂无图片</p>')
    image_preview.short_description = '图片预览'

# 扩展admin site以添加自定义视图
class CustomAdminSite(admin.AdminSite):
    site_header = '羽毛球动作分析系统管理后台'
    site_title = '羽毛球动作分析系统'
    index_title = '管理首页'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload_mat/', self.admin_view(self.upload_mat_view), name='upload_mat'),
            path('analysis_result/', self.admin_view(self.analysis_result_view), name='analysis_result'),  # 新增无参数
            path('analysis_result/<int:session_id>/', self.admin_view(self.analysis_result_view), name='analysis_result_with_id'),
            path('analysis_list/', self.admin_view(self.analysis_list_view), name='analysis_list'),  # 新增分析结果列表
        ]
        return custom_urls + urls
    
    def index(self, request, extra_context=None):
        """自定义首页，添加快速操作"""
        extra_context = extra_context or {}
        extra_context.update({
            'quick_actions': [
                {
                    'title': '上传.mat文件',
                    'url': 'upload_mat/',
                    'description': '上传.mat文件进行动作分析',
                    'icon': '📁'
                },
                {
                    'title': '查看最新分析结果',
                    'url': 'analysis_result/',
                    'description': '查看最新的分析结果和图表',
                    'icon': '📊'
                },
                {
                    'title': '分析结果列表',
                    'url': 'analysis_list/',
                    'description': '查看所有历史分析结果',
                    'icon': '📋'
                },
                {
                    'title': '数据采集会话',
                    'url': 'wxapp/datacollectionsession/',
                    'description': '管理数据采集会话',
                    'icon': '📱'
                },
                {
                    'title': '传感器数据',
                    'url': 'wxapp/sensordata/',
                    'description': '查看传感器数据记录',
                    'icon': '📡'
                },
                {
                    'title': '分析结果',
                    'url': 'wxapp/analysisresult/',
                    'description': '查看所有分析结果',
                    'icon': '📈'
                },
                {
                    'title': '微信用户',
                    'url': 'wxapp/wxuser/',
                    'description': '管理微信用户',
                    'icon': '👤'
                }
            ]
        })
        return super().index(request, extra_context)
    
    def upload_mat_view(self, request):
        """处理.mat文件上传"""
        if request.method == 'POST':
            mat_file = request.FILES.get('mat_file')
            openid = request.POST.get('openid')
            
            if not mat_file or not openid:
                messages.error(request, '请选择.mat文件和输入openid')
                return render(request, 'admin/mat_upload.html', {
                    'title': '上传.mat文件',
                    'users': WxUser.objects.all()
                })
            
            try:
                wx_user = WxUser.objects.get(openid=openid)
                
                # 保存上传的文件
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mat') as tmp_file:
                    for chunk in mat_file.chunks():
                        tmp_file.write(chunk)
                    tmp_file_path = tmp_file.name
                
                # 加载.mat文件
                mat_data = loadmat(tmp_file_path)
                
                # 处理数据并创建会话
                session_data = process_mat_data(mat_data, wx_user)
                
                # 清理临时文件
                os.unlink(tmp_file_path)
                
                messages.success(request, f'文件处理成功！会话ID: {session_data["session_id"]}')
                return render(request, 'admin/analysis_result.html', {
                    'title': '分析结果',
                    'session_id': session_data['session_id'],
                    'summary': session_data['summary']
                })
                
            except WxUser.DoesNotExist:
                messages.error(request, '用户不存在')
            except Exception as e:
                messages.error(request, f'处理失败: {str(e)}')
        
        return render(request, 'admin/mat_upload.html', {
            'title': '上传.mat文件',
            'users': WxUser.objects.all()
        })
    
    def analysis_result_view(self, request, session_id=None):
        """显示分析结果"""
        if session_id is None:
            # 如果没有指定session_id，显示最新的分析结果
            try:
                latest_analysis = AnalysisResult.objects.select_related('session').latest('analysis_time')
                session_id = latest_analysis.session.id
            except AnalysisResult.DoesNotExist:
                messages.error(request, '没有找到分析结果')
                return render(request, 'admin/mat_upload.html', {
                    'title': '上传.mat文件',
                    'users': WxUser.objects.all()
                })
        
        try:
            session = DataCollectionSession.objects.get(id=session_id)
            analysis_result = AnalysisResult.objects.get(session=session)
            
            # 生成详细报告
            report = generate_detailed_report(analysis_result, session)
            
            return render(request, 'admin/analysis_result.html', {
                'title': '分析结果',
                'session': session,
                'analysis_result': analysis_result,
                'report': report
            })
            
        except (DataCollectionSession.DoesNotExist, AnalysisResult.DoesNotExist):
            messages.error(request, '分析结果不存在')
            return render(request, 'admin/mat_upload.html', {
                'title': '上传.mat文件',
                'users': WxUser.objects.all()
            })
    
    def analysis_list_view(self, request):
        """显示分析结果列表"""
        # 获取所有分析结果，按时间倒序排列
        analysis_results = AnalysisResult.objects.select_related(
            'session__user', 'session__device_group'
        ).order_by('-analysis_time')
        
        # 支持按用户筛选
        user_filter = request.GET.get('user')
        if user_filter:
            analysis_results = analysis_results.filter(session__user__openid__icontains=user_filter)
        
        # 支持按时间范围筛选
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        if date_from:
            analysis_results = analysis_results.filter(analysis_time__gte=date_from)
        if date_to:
            analysis_results = analysis_results.filter(analysis_time__lte=date_to)
        
        # 分页
        from django.core.paginator import Paginator
        paginator = Paginator(analysis_results, 20)  # 每页20条
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'admin/analysis_list.html', {
            'title': '分析结果列表',
            'page_obj': page_obj,
            'analysis_results': page_obj.object_list,
            'user_filter': user_filter,
            'date_from': date_from,
            'date_to': date_to,
        })

# 创建自定义admin site实例
custom_admin_site = CustomAdminSite(name='custom_admin')

# 注册模型到自定义admin site
custom_admin_site.register(WxUser, WxUserAdmin)
custom_admin_site.register(DeviceBind, DeviceBindAdmin)
custom_admin_site.register(SensorData, SensorDataAdmin)
custom_admin_site.register(DeviceGroup, DeviceGroupAdmin)
custom_admin_site.register(DataCollectionSession, DataCollectionSessionAdmin)
custom_admin_site.register(AnalysisResult, AnalysisResultAdmin)
