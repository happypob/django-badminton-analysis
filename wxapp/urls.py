from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.wx_login),
    path('simple_login/', views.simple_login),  # 新增简化登录接口
    path('bind_device/', views.bind_device),
    path('upload_sensor_data/', views.upload_sensor_data),
    path('start_session/', views.start_collection_session),
    path('start_data_collection/', views.start_data_collection),
    path('end_session/', views.end_collection_session),
    path('mark_complete/', views.mark_data_collection_complete),  # 新增数据收集完成标记接口
    path('notify_esp32_start/', views.notify_esp32_start),
    path('notify_esp32_stop/', views.notify_esp32_stop),
    path('get_analysis/', views.get_analysis_result),
    path('generate_report/', views.generate_analysis_report),
    path('upload_mat/', views.upload_mat_file),
    path('get_mat_analysis/', views.get_mat_analysis_result),
    # 新增小程序数据发送接口
    path('send_data1/', views.send_data1),
    path('send_data2/', views.send_data2),
    path('send_data3/', views.send_data3),
    # 新增ESP32专用接口
    path('esp32/upload/', views.esp32_upload_sensor_data, name='esp32_upload'),
    path('esp32/batch_upload/', views.esp32_batch_upload, name='esp32_batch_upload'),
    path('esp32/mark_upload_complete/', views.esp32_mark_upload_complete, name='esp32_mark_upload_complete'),
    path('esp32/status/', views.esp32_device_status, name='esp32_status'),
    # 新增设备ID通知接口
    path('register_device_ip/', views.register_device_ip),
    path('notify_device_start/', views.notify_device_start),
    path('notify_device_stop/', views.notify_device_stop),
    path('get_device_status/', views.get_device_status),
] 