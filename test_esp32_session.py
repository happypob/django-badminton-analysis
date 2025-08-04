import requests
import json
import time

def test_esp32_session_upload():
    """测试ESP32使用会话1009上传数据"""
    
    url = "http://47.122.129.159:8000/wxapp/esp32/upload/"
    
    # 模拟ESP32的流式传输数据
    test_data = {
        "device_code": "esp32s3_multi_001",
        "sensor_type": "waist",
        "session_id": "1009",
        "data": json.dumps({
            "acc": [1.23, 2.34, 3.45],
            "gyro": [4.56, 5.67, 6.78],
            "angle": [7.89, 8.90, 9.01]
        }),
        "timestamp": str(int(time.time() * 1000)),
        "streaming": "true"
    }
    
    print(f"测试ESP32流式传输到会话1009:")
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

def test_multiple_sensors():
    """测试多个传感器同时上传"""
    
    url = "http://47.122.129.159:8000/wxapp/esp32/upload/"
    session_id = "1009"
    
    sensors = [
        {"type": "waist", "id": 1},
        {"type": "shoulder", "id": 2},
        {"type": "wrist", "id": 3},
        {"type": "racket", "id": 4}
    ]
    
    print(f"\n测试多个传感器流式传输:")
    
    for sensor in sensors:
        data = {
            "device_code": "esp32s3_multi_001",
            "sensor_type": sensor["type"],
            "session_id": session_id,
            "data": json.dumps({
                "acc": [sensor["id"] * 1.1, sensor["id"] * 1.2, sensor["id"] * 1.3],
                "gyro": [sensor["id"] * 2.1, sensor["id"] * 2.2, sensor["id"] * 2.3],
                "angle": [sensor["id"] * 3.1, sensor["id"] * 3.2, sensor["id"] * 3.3]
            }),
            "timestamp": str(int(time.time() * 1000)),
            "streaming": "true"
        }
        
        try:
            response = requests.post(url, data=data)
            print(f"传感器 {sensor['type']}: {response.status_code}")
        except Exception as e:
            print(f"传感器 {sensor['type']}: 错误 - {e}")

if __name__ == "__main__":
    test_esp32_session_upload()
    test_multiple_sensors() 