import os
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangodemo.settings')
django.setup()

from django.contrib.auth.models import User

def create_admin_user():
    try:
        # 检查是否已存在admin用户
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            # 设置密码
            user.set_password('admin123')
            user.save()
            print('成功创建admin用户，密码: admin123')
        else:
            # 更新现有用户的密码
            user.set_password('admin123')
            user.save()
            print('成功更新admin用户密码为: admin123')
            
    except Exception as e:
        print(f'创建用户失败: {str(e)}')

if __name__ == '__main__':
    create_admin_user() 