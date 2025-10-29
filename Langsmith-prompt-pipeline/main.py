"""
报告生成器主程序
提供命令行界面运行报告生成流程
"""
import sys

# 尝试配置输出编码（某些环境可能不支持）
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    # Jupyter/IPython 环境通常不需要这个配置
    pass

import argparse
from pathlib import Path
from datetime import datetime

from config.langsmith_config import LangSmithConfig
from config.azure_config import AzureConfig
from graph.graph import ReportGraphBuilder


def save_report(report: str, output_path: str):
    """
    保存报告到文件
    
    Args:
        report: 报告内容
        output_path: 输出文件路径
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✓ 报告已保存到: {output_file.absolute()}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="智能报告生成器 - 基于 LangGraph 和 LangSmith",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础使用
  python main.py --query "人工智能行业2023-2024年发展分析"
  
  # 指定参数
  python main.py --query "科技行业分析" --year-range "2024" --style concise
  
  # 保存报告到文件
  python main.py --query "金融科技报告" --output reports/fintech_2024.md
  
  # 关闭 LangSmith 追踪
  python main.py --query "快速测试" --no-trace
        """
    )
    
    # 必需参数
    parser.add_argument(
        "--query",
        required=True,
        help="报告主题或用户查询"
    )
    
    # 可选参数
    parser.add_argument(
        "--year-range",
        default="",
        help="年份范围，如 '2023-2024' 或 '2024'"
    )
    
    parser.add_argument(
        "--style",
        choices=["formal", "casual", "detailed", "concise"],
        default="",
        help="编写风格: formal(正式), casual(轻松), detailed(详细), concise(简洁)"
    )
    
    parser.add_argument(
        "--depth",
        choices=["shallow", "medium", "deep"],
        default="",
        help="分析深度: shallow(浅层), medium(中等), deep(深度)"
    )
    
    parser.add_argument(
        "--focus-areas",
        default="",
        help="关注领域，用逗号分隔，如 '技术创新,市场规模,投资趋势'"
    )
    
    # 输出选项
    parser.add_argument(
        "--output",
        "-o",
        default="",
        help="输出文件路径（不指定则只打印到控制台）"
    )
    
    # LangSmith 选项
    parser.add_argument(
        "--no-trace",
        action="store_true",
        help="关闭 LangSmith 追踪"
    )
    
    parser.add_argument(
        "--project",
        default="economic_report",
        help="LangSmith 项目名称"
    )
    
    args = parser.parse_args()
    
    # 配置 LangSmith 追踪
    if not args.no_trace:
        LangSmithConfig.enable_tracing(project_name=args.project)
    else:
        LangSmithConfig.disable_tracing()
    
    # 打印配置信息
    print("\n" + "="*60)
    print("智能报告生成器")
    print("="*60)
    print(f"\n查询: {args.query}")
    
    if args.year_range:
        print(f"年份范围: {args.year_range}")
    if args.style:
        print(f"风格: {args.style}")
    if args.depth:
        print(f"深度: {args.depth}")
    if args.focus_areas:
        print(f"关注领域: {args.focus_areas}")
    
    print(f"\nLangSmith 追踪: {'开启' if not args.no_trace else '关闭'}")
    if not args.no_trace:
        print(f"项目名称: {args.project}")
        print(f"查看追踪: https://smith.langchain.com/")
    
    # 创建 Graph 构建器
    builder = ReportGraphBuilder()
    
    # 准备初始参数
    initial_params = {}
    if args.year_range:
        initial_params["year_range"] = args.year_range
    if args.style:
        initial_params["style"] = args.style
    if args.depth:
        initial_params["depth"] = args.depth
    if args.focus_areas:
        initial_params["focus_areas"] = args.focus_areas
    
    # 运行报告生成
    try:
        print("\n开始生成报告...\n")
        
        result = builder.run(
            user_query=args.query,
            **initial_params
        )
        
        # 提取报告
        report = result.get("report", "")
        
        if not report:
            print("✗ 未能生成报告")
            sys.exit(1)
        
        # 显示元数据
        metadata = result.get("metadata", {})
        if metadata:
            print(f"\n报告元数据:")
            for key, value in metadata.items():
                print(f"  {key}: {value}")
        
        # 保存或显示报告
        if args.output:
            save_report(report, args.output)
            print(f"\n提示: 使用 Markdown 阅读器查看报告获得最佳体验")
        else:
            print("\n" + "="*60)
            print("生成的报告")
            print("="*60 + "\n")
            print(report)
            print("\n" + "="*60)
            print("\n提示: 使用 --output 参数可以保存报告到文件")
        
        # 成功退出
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n✗ 生成报告时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

