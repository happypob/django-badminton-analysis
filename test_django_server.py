import requests
import time

def test_django_server():
    """测试Django服务器是否正在运行"""
    
    # 测试基础URL
    base_urls = [
        "http://47.122.129.159:8000/",
        "http://47.122.129.159:8000/wxapp/",
        "http://47.122.129.159:8000/admin/"
    ]
    
    print("测试Django服务器状态:")
    for url in base_urls:
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {url}: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {url}: 连接失败 - 服务器可能未运行")
        except requests.exceptions.Timeout:
            print(f"⏰ {url}: 请求超时")
        except Exception as e:
            print(f"❌ {url}: 错误 - {e}")
    
    # 测试ESP32上传URL
    esp32_url = "http://47.122.129.159:8000/wxapp/esp32/upload/"
    print(f"\n测试ESP32上传URL: {esp32_url}")
    
    try:
        # 先测试GET请求
        response = requests.get(esp32_url, timeout=5)
        print(f"GET请求: {response.status_code}")
        print(f"响应内容: {response.text[:200]}...")
    except Exception as e:
        print(f"GET请求失败: {e}")
    
    try:
        # 测试POST请求
        data = {
            "device_code": "test",
            "sensor_type": "waist",
            "data": '{"acc":[1,2,3],"gyro":[4,5,6],"angle":[7,8,9]}'
        }
        response = requests.post(esp32_url, data=data, timeout=5)
        print(f"POST请求: {response.status_code}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"POST请求失败: {e}")

if __name__ == "__main__":
    test_django_server() 