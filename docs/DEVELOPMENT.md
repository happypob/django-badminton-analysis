# 开发指南

## 📋 概述

本指南介绍如何设置开发环境、代码规范和开发流程。

## 🛠️ 开发环境设置

### 系统要求
- **Python**: 3.8+
- **Node.js**: 16+ (前端开发)
- **Git**: 2.30+
- **IDE**: VS Code / PyCharm

### 1. 克隆项目
```bash
git clone <repository-url>
cd django-badminton-analysis
```

### 2. 创建虚拟环境
```bash
# 使用venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 使用conda
conda create -n badminton python=3.9
conda activate badminton
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

### 4. 环境配置
```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件
vim .env
```

### 5. 数据库设置
```bash
# 创建数据库
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 加载测试数据
python manage.py loaddata fixtures/test_data.json
```

### 6. 启动开发服务器
```bash
# 启动Django服务
python manage.py runserver

# 启动WebSocket服务
daphne -b 0.0.0.0 -p 8001 djangodemo.asgi:application

# 启动Redis (用于WebSocket)
redis-server
```

## 📁 项目结构

```
django-badminton-analysis/
├── djangodemo/              # Django项目配置
│   ├── __init__.py
│   ├── settings.py          # 项目设置
│   ├── urls.py             # 主URL配置
│   ├── asgi.py             # ASGI配置
│   └── wsgi.py             # WSGI配置
├── wxapp/                  # 主应用
│   ├── __init__.py
│   ├── models.py           # 数据模型
│   ├── views.py            # API视图
│   ├── urls.py             # 应用URL配置
│   ├── consumers.py        # WebSocket消费者
│   ├── analysis.py         # 动作分析算法
│   ├── esp32_handler.py    # ESP32数据处理
│   ├── websocket_manager.py # WebSocket管理
│   ├── admin.py            # 管理后台
│   ├── apps.py             # 应用配置
│   ├── tests.py            # 测试文件
│   └── management/         # 管理命令
│       └── commands/
├── templates/              # HTML模板
│   └── admin/
├── staticfiles/            # 静态文件
├── docs/                   # 项目文档
├── requirements.txt        # 生产依赖
├── requirements-dev.txt    # 开发依赖
├── .env.example           # 环境配置示例
├── .gitignore             # Git忽略文件
├── docker-compose.yml     # Docker配置
└── README.md              # 项目说明
```

## 🎯 开发规范

### 1. 代码风格

#### Python代码规范
- 遵循PEP 8规范
- 使用Black进行代码格式化
- 使用isort进行导入排序
- 使用flake8进行代码检查

```bash
# 安装代码检查工具
pip install black isort flake8

# 格式化代码
black .
isort .

# 检查代码
flake8 .
```

#### 代码示例
```python
# 好的代码风格
def analyze_sensor_data(sensor_data: dict, session_id: int) -> dict:
    """
    分析传感器数据
    
    Args:
        sensor_data: 传感器数据字典
        session_id: 会话ID
        
    Returns:
        分析结果字典
    """
    if not sensor_data:
        raise ValueError("传感器数据不能为空")
    
    # 数据处理逻辑
    result = process_data(sensor_data)
    
    return {
        'phase_delay': result['delay'],
        'energy_ratio': result['energy'],
        'rom_data': result['rom']
    }
```

### 2. 命名规范

#### 变量命名
```python
# 使用snake_case
user_id = 123
sensor_data = {}
device_group_code = "badminton_001"

# 常量使用UPPER_CASE
MAX_RETRY_COUNT = 3
DEFAULT_SAMPLE_RATE = 100
```

#### 函数命名
```python
# 使用动词开头
def get_user_by_openid(openid: str) -> User:
    pass

def calculate_phase_delay(data: dict) -> float:
    pass

def upload_sensor_data(data: dict) -> bool:
    pass
```

#### 类命名
```python
# 使用PascalCase
class SensorDataProcessor:
    pass

class AnalysisResult:
    pass

class WebSocketManager:
    pass
```

### 3. 文档规范

#### 函数文档
```python
def process_sensor_data(data: dict, sensor_type: str) -> dict:
    """
    处理传感器数据
    
    Args:
        data: 原始传感器数据，包含acc、gyro、angle字段
        sensor_type: 传感器类型，可选值：waist, shoulder, wrist, racket
        
    Returns:
        处理后的数据字典，包含标准化后的传感器数据
        
    Raises:
        ValueError: 当传感器类型无效时
        KeyError: 当数据缺少必要字段时
        
    Example:
        >>> data = {'acc': [1, 2, 3], 'gyro': [0.1, 0.2, 0.3]}
        >>> result = process_sensor_data(data, 'waist')
        >>> print(result['normalized_acc'])
        [0.1, 0.2, 0.3]
    """
    pass
```

#### API文档
```python
@api_view(['POST'])
def upload_sensor_data(request):
    """
    上传传感器数据
    
    POST /wxapp/upload_sensor_data/
    
    Parameters:
        session_id (int, optional): 会话ID
        device_code (str, required): 设备编码
        sensor_type (str, required): 传感器类型
        data (str, required): JSON格式的传感器数据
        
    Returns:
        200: 上传成功
        400: 参数错误
        500: 服务器错误
        
    Example:
        POST /wxapp/upload_sensor_data/
        {
            "session_id": 123,
            "device_code": "waist_sensor_001",
            "sensor_type": "waist",
            "data": "{\"acc\": [1,2,3], \"gyro\": [0.1,0.2,0.3]}"
        }
    """
    pass
```

## 🧪 测试规范

### 1. 单元测试

#### 测试文件结构
```
wxapp/
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_analysis.py
│   └── test_consumers.py
```

#### 测试示例
```python
# test_models.py
from django.test import TestCase
from django.contrib.auth.models import User
from wxapp.models import WxUser, DeviceBind

class WxUserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.wx_user = WxUser.objects.create(
            user=self.user,
            openid='test_openid_123'
        )
    
    def test_wx_user_creation(self):
        """测试微信用户创建"""
        self.assertEqual(self.wx_user.openid, 'test_openid_123')
        self.assertEqual(self.wx_user.user, self.user)
    
    def test_wx_user_str_representation(self):
        """测试字符串表示"""
        expected = f"{self.user} - test_openid_123"
        self.assertEqual(str(self.wx_user), expected)
```

### 2. 集成测试

```python
# test_views.py
from django.test import TestCase, Client
from django.urls import reverse
import json

class SensorDataUploadTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.wx_user = WxUser.objects.create(
            openid='test_openid_123'
        )
    
    def test_upload_sensor_data_success(self):
        """测试传感器数据上传成功"""
        data = {
            'device_code': 'waist_sensor_001',
            'sensor_type': 'waist',
            'data': json.dumps({
                'acc': [1, 2, 3],
                'gyro': [0.1, 0.2, 0.3]
            })
        }
        
        response = self.client.post(
            reverse('upload_sensor_data'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('msg', response.json())
```

### 3. 运行测试

```bash
# 运行所有测试
python manage.py test

# 运行特定测试
python manage.py test wxapp.tests.test_models

# 运行测试并生成覆盖率报告
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 🔄 开发流程

### 1. 分支管理

```bash
# 创建功能分支
git checkout -b feature/sensor-data-processing

# 创建修复分支
git checkout -b fix/websocket-connection-issue

# 创建发布分支
git checkout -b release/v1.2.0
```

### 2. 提交规范

```bash
# 提交信息格式
<type>(<scope>): <subject>

# 类型说明
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建过程或辅助工具的变动

# 示例
git commit -m "feat(sensor): 添加传感器数据预处理功能"
git commit -m "fix(websocket): 修复连接断开重连问题"
git commit -m "docs(api): 更新API文档"
```

### 3. 代码审查

#### Pull Request模板
```markdown
## 变更说明
- 添加了传感器数据预处理功能
- 优化了数据分析算法性能
- 修复了WebSocket连接问题

## 测试
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试完成

## 检查清单
- [ ] 代码符合项目规范
- [ ] 添加了必要的文档
- [ ] 更新了相关测试
- [ ] 没有破坏性变更
```

## 🚀 部署流程

### 1. 开发环境
```bash
# 启动开发服务器
python manage.py runserver
daphne -b 0.0.0.0 -p 8001 djangodemo.asgi:application
```

### 2. 测试环境
```bash
# 使用Docker部署测试环境
docker-compose -f docker-compose.test.yml up -d
```

### 3. 生产环境
```bash
# 使用部署脚本
./deploy.sh

# 或使用Docker
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 性能监控

### 1. 日志配置
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'wxapp': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### 2. 性能分析
```python
# 使用Django Debug Toolbar
pip install django-debug-toolbar

# 在settings.py中配置
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

## 🔧 工具配置

### 1. VS Code配置
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

### 2. Pre-commit配置
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
```

## 📞 技术支持

### 开发资源
- [Django文档](https://docs.djangoproject.com/)
- [Django Channels文档](https://channels.readthedocs.io/)
- [Python PEP 8](https://pep8.org/)

### 问题反馈
- GitHub Issues: [项目Issues页面]
- 邮件: dev@example.com
- 微信群: [开发群二维码]

### 贡献指南
1. Fork项目
2. 创建功能分支
3. 提交变更
4. 创建Pull Request
5. 等待代码审查
6. 合并到主分支
