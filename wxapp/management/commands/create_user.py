from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from wxapp.models import WxUser

class Command(BaseCommand):
    help = '创建一个指定ID的用户'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int, help='用户ID')
        parser.add_argument('--username', type=str, default='', help='用户名')
        parser.add_argument('--openid', type=str, default='', help='微信openid')

    def handle(self, *args, **options):
        user_id = options['user_id']
        username = options['username'] or f'user_{user_id}'
        openid = options['openid'] or f'openid_{user_id}'
        
        try:
            # 创建 Django 用户
            user = User.objects.create(
                id=user_id,
                username=username,
                is_staff=True,
                is_superuser=True
            )
            
            # 创建 WxUser 绑定
            wx_user = WxUser.objects.create(
                user=user,
                openid=openid
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'成功创建用户 ID: {user_id}, 用户名: {username}, openid: {openid}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'创建用户失败: {str(e)}')
            ) 