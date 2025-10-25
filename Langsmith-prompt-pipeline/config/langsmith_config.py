"""
LangSmith 配置模块
"""
import os
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class LangSmithConfig:
    """LangSmith 配置类"""
    
    # 从环境变量读取 LangSmith 配置
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "economic_report")
    
    @classmethod
    def enable_tracing(cls, project_name: Optional[str] = None):
        """
        启用 LangSmith 追踪
        
        Args:
            project_name: 项目名称，如果不提供则使用默认值
        """
        # 检查 API Key 是否存在
        if not cls.LANGSMITH_API_KEY:
            print("[WARN] LangSmith API Key 未配置，跳过追踪功能")
            print("  如需使用追踪功能，请在 .env 中设置 LANGSMITH_API_KEY")
            return
        
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = cls.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_ENDPOINT"] = cls.LANGSMITH_ENDPOINT
        os.environ["LANGCHAIN_PROJECT"] = project_name or cls.LANGSMITH_PROJECT
        
        print(f"[OK] LangSmith 追踪已启用")
        print(f"  项目: {project_name or cls.LANGSMITH_PROJECT}")
        print(f"  查看追踪: https://smith.langchain.com/o/default/projects")
    
    @classmethod
    def disable_tracing(cls):
        """关闭 LangSmith 追踪（生产环境）"""
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        print("[OK] LangSmith 追踪已关闭")
    
    @classmethod
    def get_client(cls):
        """
        获取 LangSmith Client 实例
        
        Returns:
            LangSmith Client 实例
            
        Raises:
            ValueError: API Key 未配置时抛出
        """
        if not cls.LANGSMITH_API_KEY:
            raise ValueError(
                "LangSmith API Key 未配置\n"
                "请在 .env 文件中设置 LANGSMITH_API_KEY"
            )
        
        from langsmith import Client
        
        return Client(
            api_key=cls.LANGSMITH_API_KEY,
            api_url=cls.LANGSMITH_ENDPOINT
        )


if __name__ == "__main__":
    # 测试 LangSmith 连接
    print("=" * 60)
    print("测试 LangSmith 配置")
    print("=" * 60)
    
    try:
        print(f"\nAPI Key: {'已配置' if LangSmithConfig.LANGSMITH_API_KEY else '未配置'}")
        print(f"Endpoint: {LangSmithConfig.LANGSMITH_ENDPOINT}")
        print(f"Project: {LangSmithConfig.LANGSMITH_PROJECT}")
        
        if not LangSmithConfig.LANGSMITH_API_KEY:
            print("\n[INFO] LangSmith 未配置，这是可选功能")
            print("  如需使用追踪功能，请在 .env 中设置 LANGSMITH_API_KEY")
        else:
            print("\n正在测试连接...")
            LangSmithConfig.enable_tracing()
            
            client = LangSmithConfig.get_client()
            print(f"\n✓ LangSmith 客户端创建成功")
            print(f"  API URL: {client.api_url}")
            
    except Exception as e:
        print(f"\n✗ 连接失败: {e}")

