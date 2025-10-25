"""
PromptManager 极简自动化方案 - 使用示例

展示如何使用新的自动拉取和手动推送功能
"""

from prompt_manager import PromptManager

def example_1_auto_pull():
    """示例1：自动拉取（日常使用）"""
    print("\n" + "="*70)
    print("示例1：自动拉取最新版本（日常使用）")
    print("="*70)
    
    # 初始化（默认启用自动拉取）
    manager = PromptManager()
    
    # 加载 Prompt（自动从 Hub 同步最新版本）
    config = manager.get('parameter_parser')
    # 输出：🔍 检查远程更新...
    #      ✅ 已从 Hub 同步最新版本
    
    print(f"\n加载的 Prompt: {config.get('name', 'parameter_parser')}")
    print(f"类型: {config.get('_type', 'unknown')}")
    
    # 创建 ChatPromptTemplate
    prompt = manager.create_chat_prompt(config)
    print(f"Prompt 类型: {type(prompt).__name__}")
    print(f"输入变量: {prompt.input_variables}")


def example_2_local_development():
    """示例2：本地开发（禁用自动拉取）"""
    print("\n" + "="*70)
    print("示例2：本地开发和测试")
    print("="*70)
    
    # 禁用自动拉取，使用本地版本
    manager = PromptManager(auto_pull=False)
    
    print("\n📝 步骤1：修改本地文件")
    print("   vim prompts/parameter_parser.yaml")
    print("   # 进行修改...")
    
    print("\n🧪 步骤2：本地测试")
    config = manager.get('parameter_parser')
    prompt = manager.create_chat_prompt(config)
    
    # 测试格式化
    messages = prompt.format_messages(
        user_query="生成一份关于人工智能的报告"
    )
    print(f"   测试消息数量: {len(messages)}")
    print("   ✅ 本地测试通过")


def example_3_push_to_hub():
    """示例3：推送到 Hub"""
    print("\n" + "="*70)
    print("示例3：推送本地修改到 Hub")
    print("="*70)
    
    manager = PromptManager()
    
    # 推送（包含自动测试）
    print("\n正在推送...")
    # result = manager.push('parameter_parser', with_test=True)
    
    # 模拟输出
    print("""
    ============================================================
    📤 推送 parameter_parser 到 Hub
    ============================================================
    
    📋 步骤 1/4: 验证 Prompt 格式...
    ✅ 格式验证通过
    
    🧪 步骤 2/4: 运行 LangSmith 测试...
       - 测试用例: 1
       - 质量分数: 92%
    ✅ 测试通过 (质量分: 0.92)
    
    🚢 步骤 3/4: 推送到 Hub...
    ✅ 已推送到: parameter_parser
       查看: https://smith.langchain.com/hub/parameter_parser
    
    ⏭️  步骤 4/4: 跳过版本备份
    
    ============================================================
    🎉 推送完成！
    ============================================================
    """)


def example_4_push_with_backup():
    """示例4：推送并创建版本备份"""
    print("\n" + "="*70)
    print("示例4：推送并创建版本备份")
    print("="*70)
    
    manager = PromptManager()
    
    # 推送并创建备份
    print("\n正在推送并创建版本备份...")
    # result = manager.push('parameter_parser', with_test=True, create_backup=True)
    
    # 模拟输出
    print("""
    ============================================================
    📤 推送 parameter_parser 到 Hub
    ============================================================
    
    📋 步骤 1/4: 验证 Prompt 格式...
    ✅ 格式验证通过
    
    🧪 步骤 2/4: 运行 LangSmith 测试...
    ✅ 测试通过 (质量分: 0.92)
    
    🚢 步骤 3/4: 推送到 Hub...
    ✅ 已推送到: parameter_parser
    
    💾 步骤 4/4: 创建版本备份...
    ✅ 已备份到: parameter_parser-v1.3.0
    
    ============================================================
    🎉 推送完成！
    ============================================================
    """)


def example_5_check_sync():
    """示例5：检查同步状态"""
    print("\n" + "="*70)
    print("示例5：检查同步状态")
    print("="*70)
    
    manager = PromptManager()
    
    # 检查同步状态
    manager.check_sync('parameter_parser')


def example_6_version_management():
    """示例6：版本管理"""
    print("\n" + "="*70)
    print("示例6：版本管理和回滚")
    print("="*70)
    
    manager = PromptManager()
    
    # 查看历史版本
    print("\n📦 查看历史版本:")
    versions = manager.list_versions('parameter_parser')
    
    # 回滚到指定版本（示例）
    print("\n🔄 回滚示例:")
    print("   manager.rollback('parameter_parser', 'v1.2.0')")
    print("   # 会从 Hub 拉取 parameter_parser-v1.2.0")
    print("   # 推送到 parameter_parser")
    print("   # 更新本地文件")


def main():
    """运行所有示例"""
    print("\n" + "="*70)
    print("PromptManager 极简自动化方案 - 使用示例")
    print("="*70)
    
    # 运行示例（注释掉实际调用以避免网络请求）
    example_1_auto_pull()
    example_2_local_development()
    example_3_push_to_hub()
    example_4_push_with_backup()
    example_5_check_sync()
    example_6_version_management()
    
    print("\n" + "="*70)
    print("所有示例完成！")
    print("="*70)
    
    print("\n快速参考:")
    print("  - 使用（自动拉取）: manager.get('parameter_parser')")
    print("  - 推送修改: manager.push('parameter_parser')")
    print("  - 检查状态: manager.check_sync('parameter_parser')")
    print("  - 查看版本: manager.list_versions('parameter_parser')")
    print("  - 回滚版本: manager.rollback('parameter_parser', 'v1.0.0')")
    print("\n")


if __name__ == "__main__":
    main()

