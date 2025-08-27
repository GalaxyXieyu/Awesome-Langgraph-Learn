#!/usr/bin/env python3
"""
安装 PostgreSQL checkpoint 相关依赖
"""
import subprocess
import sys
import os


def run_command(command, description):
    """运行命令并处理错误"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} 成功")
        if result.stdout:
            print(f"   输出: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败")
        print(f"   错误: {e.stderr.strip()}")
        return False


def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    print(f"🐍 Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ 需要 Python 3.8 或更高版本")
        return False
    
    print("✅ Python 版本符合要求")
    return True


def check_conda_env():
    """检查是否在 conda 环境中"""
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env:
        print(f"🐍 当前 conda 环境: {conda_env}")
        if conda_env == 'langgraph':
            print("✅ 在正确的 conda 环境中")
            return True
        else:
            print("⚠️  不在 langgraph 环境中，请运行: conda activate langgraph")
            return False
    else:
        print("⚠️  未检测到 conda 环境")
        return False


def install_dependencies():
    """安装依赖包"""
    dependencies = [
        "psycopg[binary]",  # PostgreSQL 驱动
        "psycopg2-binary",  # 备用 PostgreSQL 驱动
    ]
    
    for dep in dependencies:
        if not run_command(f"pip install {dep}", f"安装 {dep}"):
            return False
    
    return True


def test_imports():
    """测试导入"""
    test_modules = [
        ("psycopg", "PostgreSQL 驱动"),
        ("psycopg.rows", "PostgreSQL 行工厂"),
    ]
    
    print("\n🧪 测试模块导入...")
    all_success = True
    
    for module, description in test_modules:
        try:
            __import__(module)
            print(f"✅ {description} 导入成功")
        except ImportError as e:
            print(f"❌ {description} 导入失败: {e}")
            all_success = False
    
    return all_success


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 PostgreSQL Checkpoint 依赖安装脚本")
    print("=" * 60)
    
    # 检查 Python 版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查 conda 环境
    check_conda_env()
    
    print("\n" + "=" * 40)
    print("📦 开始安装依赖...")
    print("=" * 40)
    
    # 安装依赖
    if not install_dependencies():
        print("\n❌ 依赖安装失败")
        sys.exit(1)
    
    print("\n" + "=" * 40)
    print("🧪 测试安装结果...")
    print("=" * 40)
    
    # 测试导入
    if not test_imports():
        print("\n❌ 模块导入测试失败")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 PostgreSQL checkpoint 依赖安装完成！")
    print("=" * 60)
    print("\n📋 下一步:")
    print("1. 配置 PostgreSQL 数据库")
    print("2. 复制 .env.example 到 .env 并配置数据库连接")
    print("3. 运行测试: python -m config.test_checkpoint")
    print("4. 设置环境变量: export USE_POSTGRES_CHECKPOINT=true")


if __name__ == "__main__":
    main()
