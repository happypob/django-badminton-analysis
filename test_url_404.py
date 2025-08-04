import requests
import json

# 测试URL
url = "http://47.122.129.159:8000/wxapp/esp32/upload/"

# 测试数据
data = {
    "device_code": "test_device",
    "sensor_type": "waist",
    "data": json.dumps({
        "acc": [1.0, 2.0, 3.0],
        "gyro": [4.0, 5.0, 6.0],
        "angle": [7.0, 8.0, 9.0]
    })
}

print(f"测试URL: {url}")
print(f"测试数据: {data}")

try:
    response = requests.post(url, data=data)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
except Exception as e:
    print(f"请求失败: {e}")

# 测试其他URL
test_urls = [
    "http://47.122.129.159:8000/",
    "http://47.122.129.159:8000/wxapp/",
    "http://47.122.129.159:8000/wxapp/esp32/",
    "http://47.122.129.159:8000/wxapp/esp32/upload/",
    "http://47.122.129.159:8000/wxapp/esp32/batch_upload/"
]

print("\n测试所有相关URL:")
for test_url in test_urls:
    try:
        response = requests.get(test_url)
        print(f"{test_url}: {response.status_code}")
    except Exception as e:
        print(f"{test_url}: 错误 - {e}") 