@echo off
echo ========================================
echo 羽毛球动作分析系统 - 依赖安装脚本
echo ========================================
echo.

echo 正在检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python未安装或未添加到PATH
    echo 请先安装Python: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo 正在升级pip...
python -m pip install --upgrade pip

echo.
echo 正在安装项目依赖...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ❌ 依赖安装失败，尝试逐个安装...
    pip install django>=5.2.4
    pip install requests>=2.31.0
    pip install numpy>=1.24.0
    pip install scipy>=1.11.0
    pip install matplotlib>=3.7.0
    pip install pandas>=2.0.0
    pip install Pillow>=10.0.0
)

echo.
echo 正在运行数据库迁移...
python manage.py makemigrations
python manage.py migrate

echo.
echo 正在创建超级用户...
echo 请按提示输入用户名和密码...
python manage.py createsuperuser

echo.
echo ========================================
echo 🎉 安装完成！
echo ========================================
echo.
echo 启动服务器: python manage.py runserver
echo 管理后台: http://localhost:8000/admin/
echo.
pause 