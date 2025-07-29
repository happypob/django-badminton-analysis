import requests
import json
import time

# 服务器配置
BASE_URL = "http://127.0.0.1:8000"
API_PREFIX = "/wxapp"

class MiniProgramAPITester:
    def __init__(self):
        self.openid = None
        self.session_id = None
        self.device_code = "test_device_001"
        self.device_group_code = "test_group_001"
    
    def test_login(self):
        """测试微信登录"""
        print("🔐 测试微信登录...")
        
        # 模拟微信小程序登录
        data = {
            'code': 'test_code_123456'  # 模拟的微信code
        }
        
        response = requests.post(f"{BASE_URL}{API_PREFIX}/login/", data=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            self.openid = result.get('openid')
            print(f"✅ 登录成功，openid: {self.openid}")
            return True
        else:
            print("❌ 登录失败")
            return False
    
    def test_bind_device(self):
        """测试设备绑定"""
        print("\n📱 测试设备绑定...")
        
        if not self.openid:
            print("❌ 请先登录")
            return False
        
        data = {
            'openid': self.openid,
            'device_code': self.device_code
        }
        
        response = requests.post(f"{BASE_URL}{API_PREFIX}/bind_device/", data=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            print("✅ 设备绑定成功")
            return True
        else:
            print("❌ 设备绑定失败")
            return False
    
    def test_start_session(self):
        """测试开始数据采集会话"""
        print("\n📊 测试开始数据采集会话...")
        
        if not self.openid:
            print("❌ 请先登录")
            return False
        
        data = {
            'openid': self.openid,
            'device_group_code': self.device_group_code
        }
        
        response = requests.post(f"{BASE_URL}{API_PREFIX}/start_session/", data=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            self.session_id = result.get('session_id')
            print(f"✅ 会话开始成功，session_id: {self.session_id}")
            return True
        else:
            print("❌ 会话开始失败")
            return False
    
    def test_upload_sensor_data(self):
        """测试上传传感器数据"""
        print("\n📡 测试上传传感器数据...")
        
        if not self.session_id:
            print("❌ 请先开始会话")
            return False
        
        # 模拟传感器数据
        sensor_data = {
            'acc': [1.2, 0.8, 9.8],
            'gyro': [0.1, 0.2, 0.3],
            'angle': [45.0, 30.0, 60.0],
            'timestamp': int(time.time())
        }
        
        data = {
            'session_id': self.session_id,
            'device_code': self.device_code,
            'sensor_type': 'waist',
            'data': json.dumps(sensor_data)
        }
        
        response = requests.post(f"{BASE_URL}{API_PREFIX}/upload_sensor_data/", data=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            print("✅ 传感器数据上传成功")
            return True
        else:
            print("❌ 传感器数据上传失败")
            return False
    
    def test_end_session(self):
        """测试结束数据采集会话"""
        print("\n🏁 测试结束数据采集会话...")
        
        if not self.session_id:
            print("❌ 请先开始会话")
            return False
        
        data = {
            'session_id': self.session_id
        }
        
        response = requests.post(f"{BASE_URL}{API_PREFIX}/end_session/", data=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            print("✅ 会话结束成功")
            return True
        else:
            print("❌ 会话结束失败")
            return False
    
    def test_get_analysis(self):
        """测试获取分析结果"""
        print("\n📈 测试获取分析结果...")
        
        if not self.session_id:
            print("❌ 请先开始会话")
            return False
        
        params = {
            'session_id': self.session_id
        }
        
        response = requests.get(f"{BASE_URL}{API_PREFIX}/get_analysis/", params=params)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            print("✅ 分析结果获取成功")
            return True
        else:
            print("❌ 分析结果获取失败")
            return False
    
    def test_generate_report(self):
        """测试生成详细分析报告"""
        print("\n📋 测试生成详细分析报告...")
        
        if not self.session_id:
            print("❌ 请先开始会话")
            return False
        
        params = {
            'session_id': self.session_id
        }
        
        response = requests.get(f"{BASE_URL}{API_PREFIX}/generate_report/", params=params)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            print("✅ 详细报告生成成功")
            return True
        else:
            print("❌ 详细报告生成失败")
            return False
    
    def test_upload_mat_file(self):
        """测试上传.mat文件"""
        print("\n📁 测试上传.mat文件...")
        
        if not self.openid:
            print("❌ 请先登录")
            return False
        
        # 创建模拟的.mat文件
        import numpy as np
        from scipy.io import savemat
        
        # 生成测试数据
        num_samples = 50
        test_data = []
        
        for i in range(num_samples):
            row = [
                1,  # 设备ID - 腰部
                i * 0.01,  # 时间戳
                *np.random.randn(3),  # 加速度XYZ
                *np.random.randn(3),  # 角速度XYZ
                *np.random.randn(3),  # 角度XYZ
            ]
            test_data.append(row)
        
        # 添加肩部和腕部数据
        for i in range(num_samples):
            row = [
                2,  # 设备ID - 肩部
                i * 0.01,  # 时间戳
                *np.random.randn(3),  # 加速度XYZ
                *np.random.randn(3),  # 角速度XYZ
                *np.random.randn(3),  # 角度XYZ
            ]
            test_data.append(row)
        
        for i in range(num_samples):
            row = [
                4,  # 设备ID - 腕部
                i * 0.01,  # 时间戳
                *np.random.randn(3),  # 加速度XYZ
                *np.random.randn(3),  # 角速度XYZ
                *np.random.randn(3),  # 角度XYZ
            ]
            test_data.append(row)
        
        # 保存为.mat文件
        mat_data = {'allData': np.array(test_data)}
        savemat('test_upload.mat', mat_data)
        
        # 上传文件
        files = {
            'mat_file': ('test_upload.mat', open('test_upload.mat', 'rb'), 'application/octet-stream')
        }
        
        data = {
            'openid': self.openid
        }
        
        response = requests.post(f"{BASE_URL}{API_PREFIX}/upload_mat/", files=files, data=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            mat_session_id = result.get('session_id')
            print(f"✅ .mat文件上传成功，session_id: {mat_session_id}")
            
            # 获取.mat文件分析结果
            self.test_get_mat_analysis(mat_session_id)
            return True
        else:
            print("❌ .mat文件上传失败")
            return False
    
    def test_get_mat_analysis(self, session_id):
        """测试获取.mat文件分析结果"""
        print("\n📊 测试获取.mat文件分析结果...")
        
        params = {
            'session_id': session_id
        }
        
        response = requests.get(f"{BASE_URL}{API_PREFIX}/get_mat_analysis/", params=params)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            print("✅ .mat文件分析结果获取成功")
            return True
        else:
            print("❌ .mat文件分析结果获取失败")
            return False
    
    def run_full_test(self):
        """运行完整测试流程"""
        print("🚀 开始微信小程序API完整测试...")
        print("=" * 50)
        
        # 1. 登录测试
        if not self.test_login():
            return
        
        # 2. 设备绑定测试
        if not self.test_bind_device():
            return
        
        # 3. 开始会话测试
        if not self.test_start_session():
            return
        
        # 4. 上传传感器数据测试
        if not self.test_upload_sensor_data():
            return
        
        # 5. 结束会话测试
        if not self.test_end_session():
            return
        
        # 6. 获取分析结果测试
        if not self.test_get_analysis():
            return
        
        # 7. 生成详细报告测试
        if not self.test_generate_report():
            return
        
        # 8. .mat文件上传测试
        self.test_upload_mat_file()
        
        print("\n" + "=" * 50)
        print("🎉 所有API测试完成！")
    
    def run_single_test(self, test_name):
        """运行单个测试"""
        test_methods = {
            'login': self.test_login,
            'bind_device': self.test_bind_device,
            'start_session': self.test_start_session,
            'upload_sensor_data': self.test_upload_sensor_data,
            'end_session': self.test_end_session,
            'get_analysis': self.test_get_analysis,
            'generate_report': self.test_generate_report,
            'upload_mat': self.test_upload_mat_file,
        }
        
        if test_name in test_methods:
            test_methods[test_name]()
        else:
            print(f"❌ 未知的测试: {test_name}")
            print("可用的测试: " + ", ".join(test_methods.keys()))

if __name__ == "__main__":
    tester = MiniProgramAPITester()
    
    import sys
    if len(sys.argv) > 1:
        # 运行单个测试
        test_name = sys.argv[1]
        tester.run_single_test(test_name)
    else:
        # 运行完整测试
        tester.run_full_test() 