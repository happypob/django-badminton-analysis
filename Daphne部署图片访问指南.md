# Daphne 部署 - 图片访问解决方案指南

## 概述
当使用 `daphne -b 0.0.0.0 -p 8000 djangodemo.asgi:application` 启动服务器时，需要特殊配置来处理静态文件和图片访问。

## 问题分析
- Daphne 本身不处理静态文件
- 需要 Django 来直接处理图片文件的HTTP请求
- 在生产环境中需要特殊的URL配置

## 解决方案

### 1. 已修复的配置

#### Django URLs 配置 (`djangodemo/urls.py`)
✅ 已添加生产环境静态文件处理：
```python
# 生产环境 - Daphne需要这些配置来处理静态文件
if not settings.DEBUG:
    from django.views.static import serve
    from django.urls import re_path
    
    urlpatterns += [
        re_path(r'^images/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
        re_path(r'^static/(?P<path>.*)$', serve, {
            'document_root': settings.STATIC_ROOT,
        }),
    ]
```

#### Django Settings 配置 (`djangodemo/settings.py`)
✅ 已确保MEDIA配置正确：
```python
MEDIA_URL = '/images/'
MEDIA_ROOT = BASE_DIR / 'images'

# 生产环境确保目录存在
if not DEBUG:
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    os.makedirs(STATIC_ROOT, exist_ok=True)
```

### 2. 小程序图片API

#### 推荐API - 小程序专用
```
GET http://your_server_ip:8000/api/miniprogram/get_images/
```

**功能特点：**
- 自动查找最新分析图片
- 如果没有图片会自动生成
- 返回图片URL供小程序直接使用
- 包含详细的会话和分析信息

**使用方法：**
```javascript
// 小程序中调用
wx.request({
  url: 'http://your_server_ip:8000/api/miniprogram/get_images/',
  method: 'GET',
  success: function(res) {
    if (res.data.success) {
      const images = res.data.images;
      // 使用图片URL
      images.forEach(image => {
        console.log('图片URL:', image.url);
        // 可以直接用于 <image> 标签的 src 属性
      });
    }
  }
});
```

#### 获取特定会话图片
```
GET http://your_server_ip:8000/api/miniprogram/get_images/?session_id=123
```

#### 强制生成图片API
```
POST http://your_server_ip:8000/api/force_generate_image/
Content-Type: application/x-www-form-urlencoded

session_id=123
```

### 3. 其他可用API

#### 调试API
```
GET http://your_server_ip:8000/api/debug_images/
```
- 查看所有图片和目录状态
- 测试图片生成功能

#### 图片列表API
```
GET http://your_server_ip:8000/api/list_images/
```
- 列出所有可用图片
- 显示文件大小和修改时间

#### 传统API（仍可用）
```
GET http://your_server_ip:8000/api/latest_analysis_images/
```

### 4. 服务器端部署步骤

#### 步骤1：确保目录存在
```bash
mkdir -p /path/to/your/project/images
chmod 755 /path/to/your/project/images
```

#### 步骤2：重启Daphne服务
```bash
# 停止当前服务
pkill -f daphne

# 重新启动
cd /path/to/your/project
daphne -b 0.0.0.0 -p 8000 djangodemo.asgi:application
```

#### 步骤3：测试配置
```bash
# 测试图片API
curl http://localhost:8000/api/debug_images/

# 测试小程序API
curl http://localhost:8000/api/miniprogram/get_images/

# 生成测试图片
curl -X POST http://localhost:8000/api/debug_images/ -d 'action=regenerate'
```

### 5. 验证和测试

#### 本地验证
```bash
# 1. 检查图片目录
ls -la /path/to/your/project/images/

# 2. 测试图片生成
curl -X POST http://localhost:8000/api/force_generate_image/ -d 'session_id=最新会话ID'

# 3. 测试图片访问
curl -I http://localhost:8000/images/latest_multi_sensor_curve.jpg
```

#### 远程访问测试
```bash
# 替换YOUR_SERVER_IP为实际IP
curl http://YOUR_SERVER_IP:8000/api/miniprogram/get_images/
```

### 6. 小程序集成示例

#### 在小程序中获取和显示图片
```javascript
// pages/analysis/analysis.js
Page({
  data: {
    images: [],
    loading: true
  },

  onLoad: function() {
    this.loadAnalysisImages();
  },

  loadAnalysisImages: function() {
    const that = this;
    wx.request({
      url: 'http://YOUR_SERVER_IP:8000/api/miniprogram/get_images/',
      method: 'GET',
      success: function(res) {
        console.log('图片API响应:', res.data);
        
        if (res.data.success) {
          that.setData({
            images: res.data.images,
            loading: false
          });
        } else {
          wx.showToast({
            title: res.data.error || '获取图片失败',
            icon: 'none'
          });
        }
      },
      fail: function(err) {
        console.error('请求失败:', err);
        wx.showToast({
          title: '网络请求失败',
          icon: 'none'
        });
        that.setData({ loading: false });
      }
    });
  },

  // 获取特定会话的图片
  loadSessionImages: function(sessionId) {
    wx.request({
      url: `http://YOUR_SERVER_IP:8000/api/miniprogram/get_images/?session_id=${sessionId}`,
      method: 'GET',
      success: function(res) {
        // 处理响应
      }
    });
  }
});
```

#### WXML 模板
```xml
<!-- pages/analysis/analysis.wxml -->
<view class="container">
  <view wx:if="{{loading}}" class="loading">
    <text>正在加载分析图片...</text>
  </view>
  
  <view wx:else>
    <view wx:for="{{images}}" wx:key="filename" class="image-item">
      <text class="image-title">{{item.title}}</text>
      <image 
        src="{{item.url}}" 
        mode="widthFix" 
        class="analysis-image"
        bindload="onImageLoad"
        binderror="onImageError"
      />
      <text class="image-desc">{{item.description}}</text>
      <text class="image-size">大小: {{item.size}} bytes</text>
    </view>
  </view>
</view>
```

### 7. 故障排除

#### 问题1：图片无法访问 (404错误)
**解决方法：**
```bash
# 检查Daphne启动命令
ps aux | grep daphne

# 确认目录权限
ls -la /path/to/your/project/images/

# 重启服务
pkill -f daphne
daphne -b 0.0.0.0 -p 8000 djangodemo.asgi:application
```

#### 问题2：图片生成失败
**解决方法：**
```bash
# 检查Python环境
python -c "import matplotlib; print('matplotlib OK')"

# 检查目录写权限
touch /path/to/your/project/images/test.txt
rm /path/to/your/project/images/test.txt
```

#### 问题3：小程序无法获取图片
**解决方法：**
1. 检查服务器防火墙设置
2. 确认小程序网络权限配置
3. 验证API返回的URL格式

### 8. 生产环境优化

#### 性能优化
```python
# 在settings.py中添加
if not DEBUG:
    # 缓存设置
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
```

#### 日志配置
```python
# 添加到settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/path/to/logs/django.log',
        },
    },
    'loggers': {
        'wxapp.views': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## 总结

### 小程序应该使用的API：
```
主要API: GET http://your_server_ip:8000/api/miniprogram/get_images/
备用API: GET http://your_server_ip:8000/api/latest_analysis_images/
调试API: GET http://your_server_ip:8000/api/debug_images/
```

### 直接图片访问URL格式：
```
http://your_server_ip:8000/images/图片文件名.jpg
```

---
**更新时间：** 2024年1月9日  
**适用版本：** Daphne + Django 5.2+ 