"""
Gunicorn配置文件
用于生产环境部署
"""

import multiprocessing

# 服务器套接字
bind = "0.0.0.0:8000"
backlog = 2048

# 工作进程
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# 重启
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# 日志
accesslog = "-"
errorlog = "-"
loglevel = "info"

# 进程命名
proc_name = "badminton_analysis"

# 用户和组
user = None
group = None

# 临时目录
tmp_upload_dir = None

# SSL (如果需要HTTPS)
keyfile = None
certfile = None 