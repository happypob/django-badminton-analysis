#!/usr/bin/env python3
"""
依赖包安装脚本
自动检查和安装项目所需的Python包
"""

import subprocess
import sys
import importlib

def check_package(package_name):
    """检查包是否已安装"""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def install_package(package_name):
    """安装指定的包"""
    try:
        print(f"正在安装 {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name} 安装失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 检查项目依赖包...")
    print("=" * 50)
    
    # 必需的包列表
    required_packages = [
        "django",
        "requests", 
        "numpy",
        "scipy",
        "matplotlib",
        "pandas",
        "Pillow"
    ]
    
    missing_packages = []
    
    # 检查每个包
    for package in required_packages:
        if check_package(package):
            print(f"✅ {package} 已安装")
        else:
            print(f"❌ {package} 未安装")
            missing_packages.append(package)
    
    print("\n" + "=" * 50)
    
    if missing_packages:
        print(f"需要安装 {len(missing_packages)} 个包:")
        for package in missing_packages:
            print(f"  - {package}")
        
        print("\n是否要自动安装这些包? (y/n): ", end="")
        choice = input().lower()
        
        if choice in ['y', 'yes', '是']:
            print("\n开始安装...")
            failed_packages = []
            
            for package in missing_packages:
                if not install_package(package):
                    failed_packages.append(package)
            
            if failed_packages:
                print(f"\n❌ 以下包安装失败:")
                for package in failed_packages:
                    print(f"  - {package}")
                print("\n请手动安装这些包:")
                print(f"pip install {' '.join(failed_packages)}")
            else:
                print("\n🎉 所有依赖包安装完成!")
        else:
            print("\n请手动安装依赖包:")
            print(f"pip install {' '.join(missing_packages)}")
    else:
        print("🎉 所有依赖包都已安装!")
    
    print("\n" + "=" * 50)
    print("📋 项目依赖检查完成")

if __name__ == "__main__":
    main() 