"""
最终报告提取工具
"""

import json
from typing import Dict, Any, Optional


def extract_final_report(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    从state中提取最终报告
    
    Args:
        state: 工作流的最终状态
        
    Returns:
        最终报告字典，如果没有则返回None
    """
    return state.get("final_report")


def format_final_report_as_markdown(final_report: Dict[str, Any]) -> str:
    """
    将最终报告格式化为Markdown格式
    
    Args:
        final_report: 最终报告字典
        
    Returns:
        Markdown格式的报告文本
    """
    if not final_report:
        return "# 报告生成失败\n\n未找到最终报告内容。"
    
    markdown_content = []
    
    # 标题
    title = final_report.get("title", "智能研究报告")
    markdown_content.append(f"# {title}\n")
    
    # 基本信息
    topic = final_report.get("topic", "")
    total_sections = final_report.get("total_sections", 0)
    total_words = final_report.get("total_words", 0)
    generation_timestamp = final_report.get("generation_timestamp", 0)
    
    markdown_content.append("## 报告信息\n")
    markdown_content.append(f"- **研究主题**: {topic}")
    markdown_content.append(f"- **章节数量**: {total_sections}")
    markdown_content.append(f"- **总字数**: {total_words}")
    markdown_content.append(f"- **生成时间**: {format_timestamp(generation_timestamp)}")
    markdown_content.append(f"- **生成方法**: {final_report.get('generation_method', 'unknown')}\n")
    
    # 章节内容
    sections = final_report.get("sections", [])
    for i, section in enumerate(sections, 1):
        section_title = section.get("title", f"第{i}章")
        section_content = section.get("content", "")
        word_count = section.get("word_count", 0)
        
        markdown_content.append(f"## {section_title}")
        markdown_content.append(f"*字数: {word_count}*\n")
        markdown_content.append(section_content)
        markdown_content.append("\n---\n")
    
    return "\n".join(markdown_content)


def save_final_report_to_file(final_report: Dict[str, Any], filename: str = "final_report.md") -> str:
    """
    将最终报告保存到文件
    
    Args:
        final_report: 最终报告字典
        filename: 保存的文件名
        
    Returns:
        保存的文件路径
    """
    markdown_content = format_final_report_as_markdown(final_report)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return filename


def get_report_summary(final_report: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取报告摘要信息
    
    Args:
        final_report: 最终报告字典
        
    Returns:
        报告摘要字典
    """
    if not final_report:
        return {"error": "未找到最终报告"}
    
    sections = final_report.get("sections", [])
    section_summaries = []
    
    for section in sections:
        section_summary = {
            "title": section.get("title", ""),
            "word_count": section.get("word_count", 0),
            "content_preview": section.get("content", "")[:200] + "..." if len(section.get("content", "")) > 200 else section.get("content", "")
        }
        section_summaries.append(section_summary)
    
    return {
        "title": final_report.get("title", ""),
        "topic": final_report.get("topic", ""),
        "total_sections": final_report.get("total_sections", 0),
        "total_words": final_report.get("total_words", 0),
        "generation_timestamp": final_report.get("generation_timestamp", 0),
        "sections": section_summaries
    }


def format_timestamp(timestamp: float) -> str:
    """格式化时间戳"""
    if not timestamp:
        return "未知"
    
    import datetime
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def print_report_info(state: Dict[str, Any]) -> None:
    """
    打印报告信息到控制台
    
    Args:
        state: 工作流的最终状态
    """
    final_report = extract_final_report(state)
    
    if not final_report:
        print("❌ 未找到最终报告")
        return
    
    print("📊 最终报告信息:")
    print(f"  标题: {final_report.get('title', '')}")
    print(f"  主题: {final_report.get('topic', '')}")
    print(f"  章节数: {final_report.get('total_sections', 0)}")
    print(f"  总字数: {final_report.get('total_words', 0)}")
    print(f"  生成时间: {format_timestamp(final_report.get('generation_timestamp', 0))}")
    
    sections = final_report.get("sections", [])
    print(f"\n📝 章节详情:")
    for i, section in enumerate(sections, 1):
        title = section.get("title", f"第{i}章")
        word_count = section.get("word_count", 0)
        print(f"  {i}. {title} ({word_count}字)")


# 使用示例
if __name__ == "__main__":
    # 模拟一个完成的state
    sample_state = {
        "final_report": {
            "title": "人工智能发展趋势 - 智能研究报告",
            "topic": "人工智能发展趋势",
            "sections": [
                {
                    "title": "第一章：AI技术现状",
                    "content": "人工智能技术在2023年取得了重大突破...",
                    "word_count": 800
                },
                {
                    "title": "第二章：未来发展趋势",
                    "content": "未来AI技术将朝着更加智能化的方向发展...",
                    "word_count": 750
                }
            ],
            "total_sections": 2,
            "total_words": 1550,
            "generation_method": "langgraph_intelligent_research",
            "generation_timestamp": 1703123456.789
        },
        "task_completed": True
    }
    
    print_report_info(sample_state)
    
    # 保存报告
    final_report = extract_final_report(sample_state)
    if final_report:
        filename = save_final_report_to_file(final_report, "sample_report.md")
        print(f"\n📄 报告已保存到: {filename}")
