import os
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangodemo.settings')
django.setup()

from django.contrib.auth.models import User
from wxapp.models import WxUser

def create_user_with_id():
    try:
        # 创建 Django 用户，指定 ID
        user = User.objects.create(
            id=2306105560,
            username='2306105569',
            email='2306105569@qq.com',
            is_staff=True,
            is_superuser=True
        )
        
        # 创建 WxUser 绑定
        wx_user = WxUser.objects.create(
            user=user,
            openid='wx_2306105560'
        )
        
        print(f'成功创建用户:')
        print(f'  ID: {user.id}')
        print(f'  用户名: {user.username}')
        print(f'  邮箱: {user.email}')
        print(f'  openid: {wx_user.openid}')
        
    except Exception as e:
        print(f'创建用户失败: {str(e)}')

if __name__ == '__main__':
    create_user_with_id() 