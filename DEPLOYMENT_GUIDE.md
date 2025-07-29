# 🚀 羽毛球动作分析系统部署指南

## 📋 部署方案选择

### **方案1: 云服务器部署 (推荐)**
- **优点**: 完全控制、高性能、可扩展
- **适用**: 生产环境、高并发场景
- **成本**: 中等 (每月50-200元)

### **方案2: 容器化部署**
- **优点**: 环境一致、易于管理、快速部署
- **适用**: 开发测试、中小型项目
- **成本**: 低 (每月20-100元)

### **方案3: 平台即服务 (PaaS)**
- **优点**: 简单快速、自动扩展、零维护
- **适用**: 原型验证、小型项目
- **成本**: 低 (每月10-50元)

---

## 🏗️ 方案1: 云服务器部署

### **步骤1: 购买云服务器**

推荐配置：
- **CPU**: 2核心以上
- **内存**: 4GB以上
- **存储**: 50GB以上
- **系统**: Ubuntu 20.04/22.04

### **步骤2: 服务器环境准备**

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和必要工具
sudo apt install -y python3 python3-pip python3-venv nginx

# 安装PostgreSQL (可选)
sudo apt install -y postgresql postgresql-contrib
```

### **步骤3: 部署项目**

```bash
# 克隆项目
git clone your-repository-url
cd djangodemo

# 运行部署脚本
chmod +x deploy.sh
./deploy.sh
```

### **步骤4: 配置Nginx**

```bash
# 复制Nginx配置
sudo cp nginx.conf /etc/nginx/sites-available/badminton-analysis

# 启用站点
sudo ln -s /etc/nginx/sites-available/badminton-analysis /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

### **步骤5: 配置系统服务**

```bash
# 复制服务文件
sudo cp systemd.service /etc/systemd/system/badminton-analysis.service

# 修改路径
sudo nano /etc/systemd/system/badminton-analysis.service

# 启用服务
sudo systemctl enable badminton-analysis
sudo systemctl start badminton-analysis
```

---

## 🐳 方案2: Docker容器化部署

### **步骤1: 安装Docker**

```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### **步骤2: 构建和运行**

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### **步骤3: 数据库迁移**

```bash
# 运行迁移
docker-compose exec web python manage.py migrate

# 创建超级用户
docker-compose exec web python create_admin.py
```

---

## ☁️ 方案3: 平台即服务部署

### **Railway部署**

1. **注册Railway账号**
2. **连接GitHub仓库**
3. **设置环境变量**:
   ```
   DEBUG=False
   ALLOWED_HOSTS=your-app.railway.app
   SECRET_KEY=your-secret-key
   ```
4. **自动部署**

### **Render部署**

1. **注册Render账号**
2. **创建Web Service**
3. **连接GitHub仓库**
4. **设置构建命令**:
   ```bash
   pip install -r requirements.txt
   python manage.py collectstatic --noinput
   python manage.py migrate
   ```
5. **设置启动命令**:
   ```bash
   gunicorn djangodemo.wsgi:application
   ```

---

## 🔧 环境变量配置

### **必需的环境变量**

```bash
# Django设置
DEBUG=False
SECRET_KEY=your-very-secret-key-here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# 数据库设置 (如果使用PostgreSQL)
DB_NAME=badminton_db
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432
```

### **生成安全密钥**

```python
import secrets
print(secrets.token_urlsafe(50))
```

---

## 🔒 安全配置

### **SSL证书配置**

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

### **防火墙配置**

```bash
# 安装UFW
sudo apt install ufw

# 配置防火墙
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

---

## 📊 监控和维护

### **日志监控**

```bash
# 查看应用日志
sudo journalctl -u badminton-analysis -f

# 查看Nginx日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### **性能监控**

```bash
# 安装htop
sudo apt install htop

# 监控系统资源
htop
```

### **备份策略**

```bash
# 数据库备份
pg_dump badminton_db > backup_$(date +%Y%m%d).sql

# 文件备份
tar -czf backup_$(date +%Y%m%d).tar.gz media/ staticfiles/
```

---

## 🚨 故障排除

### **常见问题**

1. **端口被占用**
   ```bash
   sudo netstat -tlnp | grep :8000
   sudo kill -9 <PID>
   ```

2. **权限问题**
   ```bash
   sudo chown -R www-data:www-data /path/to/project
   sudo chmod -R 755 /path/to/project
   ```

3. **静态文件404**
   ```bash
   python manage.py collectstatic --noinput
   sudo systemctl restart nginx
   ```

### **性能优化**

1. **启用Gzip压缩**
2. **配置CDN**
3. **数据库优化**
4. **缓存配置**

---

## 📞 技术支持

- **文档**: 查看项目README
- **日志**: 检查logs/目录
- **社区**: Django官方论坛
- **监控**: 设置告警机制

---

*部署指南版本: v1.0*  
*最后更新: 2024年* 