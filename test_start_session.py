import requests
import json

def test_start_session():
    url = "http://localhost:8000/wxapp/start_session/"
    
    print("🔍 测试start_session接口...")
    
    # 测试GET请求
    try:
        response = requests.get(url, timeout=5)
        print(f"GET请求状态码: {response.status_code}")
        print(f"GET响应: {response.text}")
    except Exception as e:
        print(f"GET请求失败: {e}")
    
    # 测试POST请求
    try:
        data = {
            'openid': 'test_user_123456',
            'device_group_code': '2025001'
        }
        response = requests.post(url, data=data, timeout=5)
        print(f"POST请求状态码: {response.status_code}")
        print(f"POST响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ start_session成功!")
            print(f"会话ID: {result.get('session_id')}")
            print(f"状态: {result.get('status')}")
        else:
            print("❌ start_session失败")
            
    except Exception as e:
        print(f"POST请求失败: {e}")

if __name__ == "__main__":
    test_start_session() 