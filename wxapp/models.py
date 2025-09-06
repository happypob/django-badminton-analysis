from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class WxUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Django用户')
    openid = models.CharField(max_length=64, unique=True, verbose_name='微信OpenID')
    # 可扩展字段，如 unionid、session_key

    class Meta:
        verbose_name = '微信用户'
        verbose_name_plural = '微信用户'

    def __str__(self):
        return f"{self.user} - {self.openid}"

class DeviceBind(models.Model):
    wx_user = models.ForeignKey(WxUser, on_delete=models.CASCADE, verbose_name='微信用户')
    device_code = models.CharField(max_length=64, verbose_name='设备编码')
    bind_time = models.DateTimeField(auto_now_add=True, verbose_name='绑定时间')

    class Meta:
        verbose_name = '设备绑定'
        verbose_name_plural = '设备绑定'

    def __str__(self):
        return f"{self.wx_user.openid} - {self.device_code}"

class DeviceGroup(models.Model):
    """设备组模型"""
    group_code = models.CharField(max_length=64, unique=True, verbose_name='设备组编号')  # 设备组编号
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '设备组'
        verbose_name_plural = '设备组'
    
    def __str__(self):
        return f"设备组 {self.group_code}"

class DataCollectionSession(models.Model):
    """数据采集会话"""
    STATUS_CHOICES = [
        ('calibrating', '校准中'),
        ('collecting', '采集中'),
        ('stopping', '停止中'),
        ('analyzing', '分析中'),
        ('completed', '已完成'),
        ('stopped', '已停止'),
    ]
    
    device_group = models.ForeignKey(DeviceGroup, on_delete=models.CASCADE, verbose_name='设备组')
    user = models.ForeignKey(WxUser, on_delete=models.CASCADE, verbose_name='用户')
    start_time = models.DateTimeField(auto_now_add=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='calibrating', verbose_name='状态')
    
    class Meta:
        verbose_name = '数据采集会话'
        verbose_name_plural = '数据采集会话'
    
    def __str__(self):
        return f"会话 {self.id} - {self.device_group.group_code}"

class SensorData(models.Model):
    """传感器数据（扩展）"""
    SENSOR_TYPE_CHOICES = [
        ('waist', '腰部传感器'),
        ('shoulder', '肩部传感器'),
        ('wrist', '腕部传感器'),
        ('racket', '球拍传感器'),
        ('unknown', '未知传感器'),
    ]
    
    session = models.ForeignKey(DataCollectionSession, on_delete=models.CASCADE, null=True, verbose_name='采集会话')
    device_code = models.CharField(max_length=64, verbose_name='设备编码')
    sensor_type = models.CharField(max_length=20, choices=SENSOR_TYPE_CHOICES, default='unknown', verbose_name='传感器类型')
    data = models.TextField(verbose_name='传感器数据')  # JSON格式存储传感器数据
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='服务器时间戳')
    esp32_timestamp = models.DateTimeField(null=True, blank=True, verbose_name='ESP32采集时间戳')
    
    class Meta:
        verbose_name = '传感器数据'
        verbose_name_plural = '传感器数据'
        indexes = [
            models.Index(fields=['session', 'device_code', 'sensor_type']),
        ]

    def __str__(self):
        return f"{self.get_sensor_type_display()} - {self.device_code}"

class AnalysisResult(models.Model):
    """分析结果"""
    session = models.OneToOneField(DataCollectionSession, on_delete=models.CASCADE, verbose_name='采集会话')
    phase_delay = models.JSONField(verbose_name='时序延迟数据')  # 时序延迟数据
    energy_ratio = models.FloatField(verbose_name='能量传递效率')  # 能量传递效率
    rom_data = models.JSONField(verbose_name='关节活动度数据')  # 关节活动度
    analysis_time = models.DateTimeField(auto_now_add=True, verbose_name='分析时间')
    
    # 图片相关字段
    analysis_image = models.CharField(max_length=255, null=True, blank=True, verbose_name='分析图片路径')
    image_generated_time = models.DateTimeField(null=True, blank=True, verbose_name='图片生成时间')
    
    class Meta:
        verbose_name = '分析结果'
        verbose_name_plural = '分析结果'
    
    def __str__(self):
        return f"分析结果 {self.session.id}"
    
    def get_image_url(self):
        """获取图片完整URL"""
        if self.analysis_image:
            from django.conf import settings
            return f"{settings.MEDIA_URL}{self.analysis_image}"
        return None
    
    def has_image(self):
        """检查是否有图片"""
        return bool(self.analysis_image)

class MiniProgramData(models.Model):
    """小程序数据模型"""
    DATA_TYPE_CHOICES = [
        (1, '数据1'),
        (2, '数据2'),
        (3, '数据3'),
    ]
    
    data_type = models.IntegerField(choices=DATA_TYPE_CHOICES, verbose_name='数据类型')
    content = models.TextField(verbose_name='数据内容')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='时间戳')
    
    class Meta:
        verbose_name = '小程序数据'
        verbose_name_plural = '小程序数据'
        indexes = [
            models.Index(fields=['data_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_data_type_display()} - {self.timestamp}"
