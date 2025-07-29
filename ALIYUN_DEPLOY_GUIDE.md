# 🚀 阿里云服务器快速部署指南

## 📋 部署步骤

### **第一步：连接阿里云服务器**

1. **获取服务器信息**：
   - 服务器IP地址
   - 用户名：root
   - 密码或SSH密钥

2. **SSH连接**：
   ```bash
   ssh root@your-server-ip
   ```

### **第二步：运行快速部署脚本**

```bash
# 下载部署脚本
wget https://raw.githubusercontent.com/your-repo/quick_deploy.sh
chmod +x quick_deploy.sh

# 运行脚本
./quick_deploy.sh
```

### **第三步：上传项目文件**

#### **方法1: 使用SCP上传**
```bash
# 在本地执行
scp -r /c/Users/23061/PycharmProjects/djangodemo/* root@your-server-ip:/opt/badminton-analysis/
```

#### **方法2: 使用Git**
```bash
# 在服务器上
cd /opt/badminton-analysis
git clone your-repository-url .
```

#### **方法3: 使用SFTP工具**
- 使用FileZilla、WinSCP等工具
- 连接到服务器
- 上传项目文件到 `/opt/badminton-analysis/`

### **第四步：启动服务**

```bash
# 进入项目目录
cd /opt/badminton-analysis

# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### **第五步：配置防火墙**

```bash
# 开放必要端口
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable
```

### **第六步：配置域名（可选）**

1. **在阿里云控制台**：
   - 域名解析 → 添加记录
   - 记录类型：A
   - 主机记录：@ 或 www
   - 记录值：您的服务器IP

2. **更新Nginx配置**：
   ```bash
   # 编辑nginx.conf文件
   nano nginx.conf
   # 将 your-domain.com 替换为您的域名
   ```

3. **重启服务**：
   ```bash
   docker-compose -f docker-compose.prod.yml restart nginx
   ```

## 🔧 服务管理命令

### **启动服务**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### **停止服务**
```bash
docker-compose -f docker-compose.prod.yml down
```

### **重启服务**
```bash
docker-compose -f docker-compose.prod.yml restart
```

### **查看日志**
```bash
# 查看所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs -f web
```

### **进入容器**
```bash
# 进入Web容器
docker-compose -f docker-compose.prod.yml exec web bash

# 进入数据库容器
docker-compose -f docker-compose.prod.yml exec db psql -U postgres
```

## 📊 访问地址

- **主站**: http://your-server-ip
- **管理后台**: http://your-server-ip/admin/
- **API文档**: http://your-server-ip/

## 🔐 管理员账号

- **用户名**: admin
- **密码**: admin123

## 🚨 故障排除

### **常见问题**

1. **端口被占用**：
   ```bash
   netstat -tlnp | grep :80
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **数据库连接失败**：
   ```bash
   # 检查数据库状态
   docker-compose -f docker-compose.prod.yml logs db
   
   # 重启数据库
   docker-compose -f docker-compose.prod.yml restart db
   ```

3. **静态文件404**：
   ```bash
   # 重新收集静态文件
   docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
   ```

### **性能优化**

1. **启用Gzip压缩**：
   ```bash
   # 编辑nginx.conf
   nano nginx.conf
   # 添加 gzip 配置
   ```

2. **配置缓存**：
   ```bash
   # 在Django设置中启用缓存
   ```

## 📈 监控和维护

### **查看系统资源**
```bash
# 安装htop
apt install htop
htop
```

### **查看Docker资源**
```bash
docker stats
```

### **备份数据**
```bash
# 备份数据库
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres badminton_db > backup.sql

# 备份文件
tar -czf backup_$(date +%Y%m%d).tar.gz media/ staticfiles/
```

## 🔒 安全建议

1. **更改默认密码**
2. **配置SSL证书**
3. **定期更新系统**
4. **设置防火墙规则**
5. **监控访问日志**

---

*阿里云部署指南版本: v1.0*  
*最后更新: 2024年* 