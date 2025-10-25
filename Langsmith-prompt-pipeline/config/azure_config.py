"""
LLM 配置模块
支持 Azure OpenAI 和标准 OpenAI 两种模式
"""
import os
from typing import Union
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI, ChatOpenAI

# 加载环境变量
load_dotenv()


class LLMConfig:
    """
    统一的 LLM 配置类
    根据环境变量自动选择使用 Azure OpenAI 或标准 OpenAI
    """
    
    # 从环境变量读取配置
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "azure").lower()
    
    # Azure OpenAI 配置
    AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
    AZURE_DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT")
    AZURE_API_VERSION = os.getenv("AZURE_API_VERSION", "2024-02-15-preview")
    AZURE_API_KEY = os.getenv("AZURE_API_KEY")
    
    # 标准 OpenAI 配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
    OPENAI_ORGANIZATION = os.getenv("OPENAI_ORGANIZATION")
    
    @classmethod
    def _validate_config(cls):
        """验证必需的配置是否存在"""
        if cls.LLM_PROVIDER == "azure":
            missing = []
            if not cls.AZURE_ENDPOINT:
                missing.append("AZURE_ENDPOINT")
            if not cls.AZURE_DEPLOYMENT:
                missing.append("AZURE_DEPLOYMENT")
            if not cls.AZURE_API_KEY:
                missing.append("AZURE_API_KEY")
            
            if missing:
                raise ValueError(
                    f"Azure OpenAI 配置缺失: {', '.join(missing)}\n"
                    f"请在 .env 文件中设置这些环境变量，参考 env.example"
                )
        
        elif cls.LLM_PROVIDER == "openai":
            if not cls.OPENAI_API_KEY:
                raise ValueError(
                    "标准 OpenAI 配置缺失: OPENAI_API_KEY\n"
                    "请在 .env 文件中设置 OPENAI_API_KEY，参考 env.example"
                )
        else:
            raise ValueError(
                f"不支持的 LLM_PROVIDER: {cls.LLM_PROVIDER}\n"
                f"支持的选项: 'azure' 或 'openai'"
            )
    
    @classmethod
    def get_llm(
        cls, 
        temperature: float = 0.7, 
        streaming: bool = False
    ) -> Union[AzureChatOpenAI, ChatOpenAI]:
        """
        获取 LLM 实例（根据配置自动选择 Azure 或标准 OpenAI）
        
        Args:
            temperature: 温度参数，控制输出的随机性 (0.0-1.0)
            streaming: 是否启用流式输出
            
        Returns:
            LLM 实例（AzureChatOpenAI 或 ChatOpenAI）
            
        Raises:
            ValueError: 配置缺失或无效时抛出
        """
        cls._validate_config()
        
        if cls.LLM_PROVIDER == "azure":
            return AzureChatOpenAI(
                azure_endpoint=cls.AZURE_ENDPOINT,
                azure_deployment=cls.AZURE_DEPLOYMENT,
                api_version=cls.AZURE_API_VERSION,
                api_key=cls.AZURE_API_KEY,
                temperature=temperature,
                streaming=streaming,
            )
        else:  # openai
            kwargs = {
                "model": cls.OPENAI_MODEL,
                "api_key": cls.OPENAI_API_KEY,
                "temperature": temperature,
                "streaming": streaming,
            }
            
            if cls.OPENAI_API_BASE:
                kwargs["base_url"] = cls.OPENAI_API_BASE
            if cls.OPENAI_ORGANIZATION:
                kwargs["organization"] = cls.OPENAI_ORGANIZATION
            
            return ChatOpenAI(**kwargs)
    
    @classmethod
    def get_fast_llm(cls) -> Union[AzureChatOpenAI, ChatOpenAI]:
        """获取快速推理的 LLM（低温度）"""
        return cls.get_llm(temperature=0.3)
    
    @classmethod
    def get_creative_llm(cls) -> Union[AzureChatOpenAI, ChatOpenAI]:
        """获取创造性输出的 LLM（高温度）"""
        return cls.get_llm(temperature=0.9)


# 向后兼容：保留 AzureConfig 作为别名
class AzureConfig(LLMConfig):
    """
    向后兼容的 Azure 配置类
    实际使用 LLMConfig，支持 Azure 和标准 OpenAI
    """
    pass


if __name__ == "__main__":
    # 测试连接
    print("=" * 60)
    print("测试 LLM 配置")
    print("=" * 60)
    
    try:
        # 显示当前配置
        provider = LLMConfig.LLM_PROVIDER
        print(f"\n当前 LLM 提供商: {provider.upper()}")
        
        if provider == "azure":
            print(f"  Endpoint: {LLMConfig.AZURE_ENDPOINT}")
            print(f"  Deployment: {LLMConfig.AZURE_DEPLOYMENT}")
            print(f"  API Version: {LLMConfig.AZURE_API_VERSION}")
        else:
            print(f"  Model: {LLMConfig.OPENAI_MODEL}")
            if LLMConfig.OPENAI_API_BASE:
                print(f"  Base URL: {LLMConfig.OPENAI_API_BASE}")
        
        # 测试连接
        print("\n正在测试连接...")
        llm = LLMConfig.get_llm()
        response = llm.invoke("你好，请回复'连接成功'")
        print(f"\n✓ LLM 连接成功!")
        print(f"  响应: {response.content}")
        
    except ValueError as e:
        print(f"\n✗ 配置错误: {e}")
        print("\n请按照以下步骤设置配置:")
        print("  1. 复制 env.example 为 .env")
        print("  2. 在 .env 中填写你的配置信息")
    except Exception as e:
        print(f"\n✗ 连接失败: {e}")

