import requests
import time

def test_server():
    url = "http://127.0.0.1:8000/wxapp/test_udp_broadcast/"
    
    print("🔍 测试Django服务器...")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            print("✅ 服务器运行正常!")
            return True
        else:
            print("❌ 服务器响应异常")
            return False
            
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

if __name__ == "__main__":
    print("等待服务器启动...")
    time.sleep(3)
    test_server() 