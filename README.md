# 羽毛球动作分析系统

## 📋 项目概述

基于Django的羽毛球动作分析系统，支持多传感器数据采集、实时动作分析和结果可视化。系统采用WebSocket进行实时通信，支持微信小程序端和ESP32硬件端。

## 🏗️ 技术架构

- **后端框架**: Django 5.2 + Django Channels
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **实时通信**: WebSocket (Daphne)
- **前端**: 微信小程序
- **硬件**: ESP32多传感器系统
- **部署**: Docker + Nginx

## 📁 项目结构

```
django-badminton-analysis/
├── djangodemo/           # Django项目配置
│   ├── settings.py       # 项目设置
│   ├── urls.py          # 主URL配置
│   └── asgi.py          # ASGI配置
├── wxapp/               # 主应用
│   ├── models.py        # 数据模型
│   ├── views.py         # API视图
│   ├── consumers.py     # WebSocket消费者
│   └── analysis.py      # 动作分析算法
├── templates/           # HTML模板
├── staticfiles/         # 静态文件
├── docs/               # 项目文档
├── requirements.txt     # Python依赖
├── docker-compose.yml   # Docker配置
└── deploy.sh           # 部署脚本
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Django 5.2+
- Redis (用于WebSocket)
- Node.js (用于前端开发)

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd django-badminton-analysis
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **数据库迁移**
   ```bash
   python manage.py migrate
   ```

4. **启动服务**
   ```bash
   python manage.py runserver
   ```

5. **启动WebSocket服务**
   ```bash
   daphne -b 0.0.0.0 -p 8001 djangodemo.asgi:application
   ```

## 📚 文档

- [API文档](docs/API.md) - 完整的API接口文档
- [部署指南](docs/DEPLOYMENT.md) - 生产环境部署指南
- [ESP32集成](docs/ESP32_INTEGRATION.md) - 硬件集成文档
- [开发指南](docs/DEVELOPMENT.md) - 开发环境配置

## 🔧 主要功能

- **用户管理**: 微信用户登录和绑定
- **设备管理**: ESP32设备绑定和管理
- **数据采集**: 多传感器实时数据采集
- **动作分析**: 基于机器学习的动作分析算法
- **结果可视化**: 分析结果图表生成
- **实时通信**: WebSocket实时数据传输

## 🛠️ 开发

### 代码规范

- 使用Python PEP 8代码规范
- 使用Django最佳实践
- 所有API接口需要文档注释

### 测试

```bash
python manage.py test
```

## 📄 许可证

本项目采用MIT许可证。

## 🤝 贡献

欢迎提交Issue和Pull Request。

## 📞 联系方式

如有问题，请联系开发团队。
