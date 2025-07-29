import requests
import json

def test_mat_upload():
    """测试.mat文件上传功能"""
    
    # 测试参数
    url = "http://127.0.0.1:8000/wxapp/upload_mat/"
    openid = "wx_2306105560"  # 使用之前创建的用户
    
    # 模拟.mat文件上传
    files = {
        'mat_file': ('test_data.mat', open('your_test_file.mat', 'rb'), 'application/octet-stream')
    }
    
    data = {
        'openid': openid
    }
    
    try:
        response = requests.post(url, files=files, data=data)
        print("响应状态码:", response.status_code)
        print("响应内容:", response.json())
        
        if response.status_code == 200:
            result = response.json()
            session_id = result.get('session_id')
            
            # 获取分析结果
            analysis_url = f"http://127.0.0.1:8000/wxapp/get_mat_analysis/?session_id={session_id}"
            analysis_response = requests.get(analysis_url)
            
            print("\n分析结果:")
            print("状态码:", analysis_response.status_code)
            print("内容:", analysis_response.json())
            
    except Exception as e:
        print(f"测试失败: {str(e)}")

if __name__ == "__main__":
    print("请确保:")
    print("1. Django服务器正在运行")
    print("2. 将你的.mat文件重命名为 'your_test_file.mat' 并放在项目根目录")
    print("3. 文件包含 'allData' 字段")
    
    # 检查文件是否存在
    import os
    if os.path.exists('your_test_file.mat'):
        test_mat_upload()
    else:
        print("\n错误: 找不到 'your_test_file.mat' 文件")
        print("请将你的测试数据文件重命名并放在项目根目录") 