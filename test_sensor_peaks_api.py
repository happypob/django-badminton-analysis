#!/usr/bin/env python
"""
测试传感器峰值合角速度API
"""
import requests
import json

def test_sensor_peaks_api():
    """测试传感器峰值API"""
    base_url = "http://localhost:8000/wxapp"
    
    # 测试参数
    session_id = 1  # 请根据实际情况修改
    
    print("🧪 测试传感器峰值合角速度API")
    print("=" * 50)
    
    # 构建请求URL
    url = f"{base_url}/get_sensor_peaks/"
    params = {"session_id": session_id}
    
    try:
        print(f"📡 发送请求到: {url}")
        print(f"📋 参数: {params}")
        
        # 发送GET请求
        response = requests.get(url, params=params)
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📄 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API调用成功!")
            print("📈 峰值合角速度数据:")
            print(f"  腰部峰值: {data.get('waist_peak', 'N/A')}")
            print(f"  肩部峰值: {data.get('shoulder_peak', 'N/A')}")
            print(f"  腕部峰值: {data.get('wrist_peak', 'N/A')}")
            print(f"  数据数组: {data.get('data', 'N/A')}")
            print(f"  峰值对象: {data.get('peaks', 'N/A')}")
            print(f"  会话信息: {data.get('session_info', 'N/A')}")
            
            # 验证前端期望的格式
            print("\n🔍 验证前端兼容性:")
            waist = data.get('waist_peak') or data.get('peaks', {}).get('waist') or (data.get('data', [])[0] if data.get('data') else None)
            shoulder = data.get('shoulder_peak') or data.get('peaks', {}).get('shoulder') or (data.get('data', [])[1] if len(data.get('data', [])) > 1 else None)
            wrist = data.get('wrist_peak') or data.get('peaks', {}).get('wrist') or (data.get('data', [])[2] if len(data.get('data', [])) > 2 else None)
            
            print(f"  ✅ 腰部数据: {waist}")
            print(f"  ✅ 肩部数据: {shoulder}")
            print(f"  ✅ 腕部数据: {wrist}")
            
            if all(isinstance(x, (int, float)) for x in [waist, shoulder, wrist]):
                print("  ✅ 所有数据都是有效数值")
            else:
                print("  ⚠️ 部分数据不是有效数值")
                
        else:
            print("❌ API调用失败!")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败! 请确保Django服务器正在运行")
        print("💡 启动命令: python manage.py runserver")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")

def test_api_without_session():
    """测试不带session_id的请求"""
    base_url = "http://localhost:8000/wxapp"
    url = f"{base_url}/get_sensor_peaks/"
    
    print("\n🧪 测试不带session_id的请求")
    print("=" * 50)
    
    try:
        response = requests.get(url)
        print(f"📊 响应状态码: {response.status_code}")
        if response.status_code == 400:
            print("✅ 正确返回400错误")
            print(f"错误信息: {response.json()}")
        else:
            print("❌ 应该返回400错误")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

if __name__ == "__main__":
    test_sensor_peaks_api()
    test_api_without_session()
