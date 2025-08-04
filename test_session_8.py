import requests
import json
import time

def test_session_8():
    """测试会话8的API"""
    
    url = "http://47.122.129.159:8000/wxapp/esp32/upload/"
    
    test_data = {
        "device_code": "esp32s3_multi_001",
        "sensor_type": "waist",
        "session_id": "8",
        "data": json.dumps({
            "acc": [1.23, 2.34, 3.45],
            "gyro": [4.56, 5.67, 6.78],
            "angle": [7.89, 8.90, 9.01]
        }),
        "timestamp": str(int(time.time() * 1000)),
        "streaming": "true"
    }
    
    print(f"测试会话8的ESP32流式传输:")
    print(f"URL: {url}")
    print(f"数据: {test_data}")
    
    try:
        response = requests.post(url, data=test_data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            print("✅ 上传成功!")
        else:
            print("❌ 上传失败!")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_session_8() 