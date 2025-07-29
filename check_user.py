import sqlite3

def check_user_in_database():
    # 连接到数据库
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    print("=== Django 用户表 (auth_user) ===")
    cursor.execute("SELECT id, username, email, is_staff, is_superuser FROM auth_user WHERE id = 2306105560")
    user = cursor.fetchone()
    if user:
        print(f"ID: {user[0]}")
        print(f"用户名: {user[1]}")
        print(f"邮箱: {user[2]}")
        print(f"是员工: {user[3]}")
        print(f"是超级用户: {user[4]}")
    else:
        print("未找到用户")
    
    print("\n=== 微信用户绑定表 (wxapp_wxuser) ===")
    cursor.execute("SELECT id, user_id, openid FROM wxapp_wxuser WHERE user_id = 2306105560")
    wx_user = cursor.fetchone()
    if wx_user:
        print(f"绑定ID: {wx_user[0]}")
        print(f"用户ID: {wx_user[1]}")
        print(f"OpenID: {wx_user[2]}")
    else:
        print("未找到微信用户绑定")
    
    print("\n=== 所有 Django 用户 ===")
    cursor.execute("SELECT id, username, email FROM auth_user")
    users = cursor.fetchall()
    for user in users:
        print(f"ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}")
    
    conn.close()

if __name__ == '__main__':
    check_user_in_database() 