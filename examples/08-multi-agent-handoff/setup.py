"""
Multi-Agent Handoff项目设置脚本

用于安装依赖和初始化环境
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    """运行命令并处理错误"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} 完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败:")
        print(f"错误: {e.stderr}")
        return False


def check_python_version():
    """检查Python版本"""
    python_version = sys.version_info
    if python_version < (3, 8):
        print("❌ Python版本过低，需要Python 3.8或更高版本")
        return False
    print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    return True


def setup_environment():
    """设置环境"""
    print("🚀 开始设置Multi-Agent Handoff环境")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        return False
    
    # 获取项目根目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # 创建虚拟环境 (使用uv)
    if not run_command("uv venv -p 3.11", "创建虚拟环境"):
        # 如果uv不可用，使用标准方法
        if not run_command("python -m venv .venv", "创建虚拟环境 (使用venv)"):
            return False
    
    # 激活虚拟环境并安装依赖
    if os.name == 'nt':  # Windows
        activate_cmd = ".venv\\Scripts\\activate"
    else:  # Unix/Linux/macOS
        activate_cmd = "source .venv/bin/activate"
    
    install_cmd = f"{activate_cmd} && pip install -r requirements.txt"
    if not run_command(install_cmd, "安装项目依赖"):
        return False
    
    # 创建环境变量文件
    env_file = project_root / ".env"
    if not env_file.exists():
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("""# Multi-Agent Handoff 环境变量配置
# 
# 请根据你使用的LLM提供商设置相应的API密钥

# OpenAI API密钥
# OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API密钥  
# ANTHROPIC_API_KEY=your_anthropic_api_key_here

# 可选: 设置代理 (如果需要)
# HTTP_PROXY=http://your-proxy:port
# HTTPS_PROXY=https://your-proxy:port
""")
        print("✅ 创建环境变量模板文件 (.env)")
        print("⚠️  请编辑 .env 文件，添加你的API密钥")
    
    # 创建测试配置
    test_config = project_root / "test_config.json"
    if not test_config.exists():
        import json
        config = {
            "default_llm": "openai",
            "test_timeout": 300,
            "enable_streaming": True,
            "enable_debug": False
        }
        with open(test_config, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("✅ 创建测试配置文件 (test_config.json)")
    
    print("\n🎉 环境设置完成!")
    print("\n📋 下一步:")
    print("1. 编辑 .env 文件，添加你的API密钥")
    print("2. 激活虚拟环境:")
    if os.name == 'nt':
        print("   .venv\\Scripts\\activate")
    else:
        print("   source .venv/bin/activate")
    print("3. 运行测试: python test.py")
    
    return True


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
Multi-Agent Handoff 设置脚本

用法:
  python setup.py        # 设置完整环境
  python setup.py --help # 显示此帮助信息

此脚本将:
1. 检查Python版本
2. 创建虚拟环境
3. 安装项目依赖
4. 创建环境配置文件
""")
        return 0
    
    try:
        success = setup_environment()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n❌ 安装被用户中断")
        return 1
    except Exception as e:
        print(f"❌ 安装过程中发生错误: {e}")
        return 1


if __name__ == "__main__":
    exit(main())