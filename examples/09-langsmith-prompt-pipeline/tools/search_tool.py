"""
联网搜索工具模块
使用 Perplexity 官方 SDK 进行在线搜索
"""
from typing import List, Dict, Any, Optional
import os
import time
import random
from perplexity import Perplexity

class SearchTool:
    """搜索工具类 - 使用 Perplexity 官方 SDK"""
    
    def __init__(
        self, 
        use_perplexity: bool = True,
        perplexity_api_key: Optional[str] = None,
        use_tavily: bool = False,
        tavily_api_key: Optional[str] = None,
        max_retries: int = 3
    ):
        """
        初始化搜索工具
        
        Args:
            use_perplexity: 是否使用 Perplexity API
            perplexity_api_key: Perplexity API Key（可选，默认从环境变量读取）
            use_tavily: 是否使用 Tavily API（备选）
            tavily_api_key: Tavily API Key（备选）
            max_retries: 最大重试次数
        """
        self.search_type = None
        self.max_retries = max_retries
        
        # 优先使用 Perplexity
        if use_perplexity:
            # 从参数或环境变量获取 API Key
            api_key = perplexity_api_key or os.getenv("PERPLEXITY_API_KEY")
            
            if api_key:
                try:
                    self.perplexity_client = Perplexity(api_key=api_key)
                    self.search_type = "perplexity"
                    print("[OK] Perplexity SDK 初始化成功")
                except Exception as e:
                    print(f"[WARN] Perplexity SDK 初始化失败: {e}")
            else:
                print("[WARN] 未找到 PERPLEXITY_API_KEY 环境变量")
        
        # 备选：Tavily
        if not self.search_type and use_tavily:
            tavily_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
            if tavily_key:
                try:
                    from tavily import TavilyClient
                    self.tavily_client = TavilyClient(api_key=tavily_key)
                    self.search_type = "tavily"
                    print("[OK] Tavily 搜索客户端初始化成功")
                except ImportError:
                    print("[WARN] Tavily 库未安装")
                except Exception as e:
                    print(f"[WARN] Tavily 客户端初始化失败: {e}")
        
        if not self.search_type:
            raise ValueError(
                "无法初始化搜索工具。请提供有效的 API Key 或设置环境变量：\n"
                "- PERPLEXITY_API_KEY\n"
                "- TAVILY_API_KEY"
            )
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        执行搜索
        
        Args:
            query: 搜索查询
            max_results: 最大结果数量
            
        Returns:
            搜索结果列表
            
        Raises:
            Exception: 搜索失败时抛出异常
        """
        if self.search_type == "perplexity":
            return self._search_with_retry(
                self._perplexity_search, 
                query, 
                max_results
            )
        elif self.search_type == "tavily":
            return self._search_with_retry(
                self._tavily_search, 
                query, 
                max_results
            )
        else:
            raise ValueError("未配置有效的搜索服务")
    
    def _search_with_retry(
        self, 
        search_func, 
        query: str, 
        max_results: int
    ) -> List[Dict[str, Any]]:
        """
        带重试机制的搜索
        
        使用指数退避策略处理临时性错误和速率限制
        
        Args:
            search_func: 实际执行搜索的函数
            query: 搜索查询
            max_results: 最大结果数量
            
        Returns:
            搜索结果列表
            
        Raises:
            Exception: 重试失败后抛出最后一次的异常
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return search_func(query, max_results)
            
            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()
                
                # 判断是否应该重试
                should_retry = any(
                    keyword in error_msg 
                    for keyword in ['timeout', 'rate limit', 'connection', 'temporarily']
                )
                
                if not should_retry or attempt == self.max_retries - 1:
                    print(f"[WARN] 搜索失败（第 {attempt + 1}/{self.max_retries} 次）: {e}")
                    break
                
                # 指数退避
                delay = (2 ** attempt) + random.uniform(0, 1)
                print(f"[WARN] 搜索失败（第 {attempt + 1}/{self.max_retries} 次），{delay:.1f}秒后重试...")
                time.sleep(delay)
        
        # 所有重试失败，抛出异常
        raise Exception(f"搜索失败（已重试 {self.max_retries} 次）: {last_exception}")
    
    def _perplexity_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        使用 Perplexity Search API 进行搜索
        
        使用 Perplexity 的 search.create() 方法
        
        Args:
            query: 搜索查询
            max_results: 最大结果数量
            
        Returns:
            搜索结果列表
        """
        try:
            print(f"  [SEARCH] 使用 Perplexity Search API: {query}")
            
            # 使用 Search API（正确的参数）
            search = self.perplexity_client.search.create(
                query=query,
                max_results=max_results,
                max_tokens_per_page=1024  # 每页最大 token 数
            )
            
            # 解析结果
            results = []
            for result in search.results:
                results.append({
                    'title': result.title,
                    'url': result.url,
                    'content': getattr(result, 'snippet', '') or getattr(result, 'text', ''),
                    'score': getattr(result, 'score', 1.0),
                    'published_date': getattr(result, 'published_date', None)
                })
            
            print(f"[OK] Perplexity 搜索完成: 获取 {len(results)} 条结果")
            return results
            
        except Exception as e:
            # 如果 Search API 失败，降级到 Chat Completions API
            print(f"  [WARN] Search API 失败: {e}")
            print(f"  [INFO] 降级到 Chat Completions API...")
            return self._perplexity_chat(query, max_results)
    
    def _perplexity_chat(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        使用 Perplexity Chat Completions API 进行搜索
        
        Perplexity 的在线搜索模型通过 Chat Completions API 提供搜索功能
        
        Args:
            query: 搜索查询
            max_results: 最大结果数量
            
        Returns:
            搜索结果列表
        """
        print(f"  执行在线搜索...")
        
        # 构建搜索提示
        search_prompt = f"""
            请搜索并总结关于"{query}"的最新信息。

            请提供：
            1. 关键发现和数据
            2. 重要趋势
            3. 统计数字和具体信息
            4. 时间范围内的发展变化

            请用中文回答，内容要详实、有数据支撑。
        """
        
        # 调用 Chat Completions API
        response = self.perplexity_client.chat.completions.create(
            model="llama-3.1-sonar-large-128k-online",  # 在线搜索模型
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的研究助手，擅长搜索和分析信息。请提供详细、准确的信息。"
                },
                {
                    "role": "user",
                    "content": search_prompt
                }
            ],
            temperature=0.2,
            max_tokens=2000
        )
        
        # 提取内容和引用
        content = response.choices[0].message.content
        citations = getattr(response, 'citations', [])
        
        # 构建结果
        results = [{
            'title': f'Perplexity 搜索结果: {query}',
            'url': citations[0] if citations else 'https://www.perplexity.ai/',
            'content': content,
            'score': 1.0,
            'citations': citations
        }]
        
        # 如果有多个引用，创建额外的结果条目
        for i, citation in enumerate(citations[:max_results-1], 1):
            results.append({
                'title': f'引用来源 {i}',
                'url': citation,
                'content': f'参考来源：{citation}',
                'score': 0.8,
                'citations': [citation]
            })
        
        print(f"[OK] Perplexity Chat 搜索完成: 获取 {len(results)} 条结果，{len(citations)} 个引用")
        
        return results[:max_results]
    
    def _tavily_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        使用 Tavily API 进行搜索（备选方案）
        
        Args:
            query: 搜索查询
            max_results: 最大结果数量
            
        Returns:
            搜索结果列表
        """
        print(f"  [SEARCH] 使用 Tavily Search API: {query}")
        
        response = self.tavily_client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced"
        )
        
        results = []
        for item in response.get('results', []):
            results.append({
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'content': item.get('content', ''),
                'score': item.get('score', 0.0)
            })
        
        print(f"[OK] Tavily 搜索完成: 获取 {len(results)} 条结果")
        return results
    
    def format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """
        格式化搜索结果为易读的文本
        
        Args:
            results: 搜索结果列表
            
        Returns:
            格式化后的文本
        """
        if not results:
            return "未找到相关搜索结果。"
        
        formatted_parts = []
        for i, result in enumerate(results, 1):
            # 基本信息
            formatted_parts.append(f"""
            ### 来源 {i}: {result.get('title', '未知标题')}

            **URL**: {result.get('url', 'N/A')}
            """)
                        
            # 发布日期（如果有）
            if result.get('published_date'):
                formatted_parts.append(f"**发布日期**: {result['published_date']}\n")
            
            # 内容
            formatted_parts.append(f"""
            **内容**:
            {result.get('content', '无内容')}
            """)
            
            # 引用来源（如果有）
            if 'citations' in result and result['citations']:
                formatted_parts.append(f"\n**引用来源**:")
                for citation in result['citations'][:5]:  # 最多显示 5 个引用
                    formatted_parts.append(f"- {citation}")
            
            formatted_parts.append("\n---\n")
        
        return "\n".join(formatted_parts)


# 测试代码
if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    
    print("=" * 60)
    print("测试 Perplexity 搜索工具（使用官方 SDK）")
    print("=" * 60)
    print()
    
    # 加载环境变量
    load_dotenv()
    
    # 检查环境变量
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("[ERROR] 未找到 PERPLEXITY_API_KEY 环境变量")
        print()
        print("请设置环境变量:")
        print("  setx PERPLEXITY_API_KEY \"your_api_key_here\"")
        print()
        print("或创建 .env 文件并添加:")
        print("  PERPLEXITY_API_KEY=your_api_key_here")
        sys.exit(1)
    
    try:
        # 初始化搜索工具
        search = SearchTool(use_perplexity=True)
        
        # 测试搜索
        query = "人工智能行业2024-2025年发展趋势和市场规模分析"
        print(f"搜索查询: {query}")
        print()
        
        results = search.search(query, max_results=3)
        
        print()
        print(f"结果数量: {len(results)}")
        print()
        
        # 格式化输出
        formatted = search.format_search_results(results)
        print("格式化结果:")
        print("=" * 60)
        
        # 限制输出长度
        if len(formatted) > 2000:
            print(formatted[:2000] + "\n\n... (输出已截断) ...")
        else:
            print(formatted)
        
        print()
        print("[OK] 测试完成")
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
