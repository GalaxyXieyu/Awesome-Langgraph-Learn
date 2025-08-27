"""测试 checkpoint 功能"""
import asyncio
import uuid
from datetime import datetime
from config.checkpoint import ResearchPostgresSaver
from config.database import get_database_url, print_database_config


def generate_test_data():
    """生成测试数据"""
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    thread_id = f"test_thread_{uuid.uuid4().hex[:8]}"
    user_id = "test_user_001"
    
    config = {
        "configurable": {
            "thread_id": thread_id,
            "session_id": session_id, 
            "user_id": user_id,
            "topic": "AI 发展趋势研究测试",
            "task_type": "research"
        }
    }
    
    checkpoint = {
        "v": 4,
        "ts": datetime.now().isoformat(),
        "id": f"checkpoint_{uuid.uuid4().hex[:8]}",
        "channel_values": {
            "topic": "AI 发展趋势研究测试",
            "current_step": "outline_generation",
            "messages": [
                {"role": "user", "content": "请研究AI发展趋势"},
                {"role": "assistant", "content": "我将为您研究AI发展趋势..."}
            ],
            "outline": {
                "sections": [
                    {"title": "AI技术现状", "description": "当前AI技术发展水平"},
                    {"title": "未来趋势", "description": "AI技术发展方向"}
                ]
            }
        },
        "channel_versions": {
            "__start__": 1,
            "topic": 1,
            "messages": 2,
            "outline": 1
        },
        "versions_seen": {
            "__input__": {},
            "__start__": {"__start__": 1}
        }
    }
    
    metadata = {
        "step": 1,
        "source": "test",
        "timestamp": datetime.now().isoformat(),
        "node_name": "outline_generator"
    }
    
    return config, checkpoint, metadata


async def test_checkpoint():
    """测试基础 checkpoint 功能"""
    print("=" * 60)
    print("🧪 开始测试 ResearchPostgresSaver 功能")
    print("=" * 60)
    
    # 打印数据库配置
    print_database_config()
    print()
    
    # 创建 checkpointer
    print("🔧 初始化 checkpointer...")
    try:
        checkpointer = ResearchPostgresSaver()
        print("✅ checkpointer 初始化成功")
    except Exception as e:
        print(f"❌ checkpointer 初始化失败: {e}")
        return
    
    # 创建表结构
    print("\n🏗️  设置数据库表结构...")
    try:
        checkpointer.setup()
        print("✅ 表结构创建成功")
    except Exception as e:
        print(f"❌ 表结构创建失败: {e}")
        return
    
    # 生成测试数据
    print("\n📝 生成测试数据...")
    config, checkpoint, metadata = generate_test_data()
    print(f"✅ 测试数据生成成功:")
    print(f"  - Session ID: {config['configurable']['session_id']}")
    print(f"  - Thread ID: {config['configurable']['thread_id']}")
    print(f"  - User ID: {config['configurable']['user_id']}")
    print(f"  - Topic: {config['configurable']['topic']}")
    
    # 测试存储
    print("\n💾 测试存储 checkpoint...")
    try:
        result_config = checkpointer.put(config, checkpoint, metadata, {})
        print("✅ checkpoint 存储成功")
        print(f"  - 返回配置: {result_config['configurable']['thread_id']}")
    except Exception as e:
        print(f"❌ checkpoint 存储失败: {e}")
        return
    
    # 测试读取
    print("\n📖 测试读取 checkpoint...")
    try:
        retrieved = checkpointer.get_tuple(config)
        if retrieved:
            print("✅ checkpoint 读取成功")
            print(f"  - Topic: {retrieved.checkpoint['channel_values']['topic']}")
            print(f"  - Current Step: {retrieved.checkpoint['channel_values']['current_step']}")
            print(f"  - Messages Count: {len(retrieved.checkpoint['channel_values']['messages'])}")
        else:
            print("❌ checkpoint 读取失败: 未找到数据")
            return
    except Exception as e:
        print(f"❌ checkpoint 读取失败: {e}")
        return
    
    # 测试列表
    print("\n📋 测试列出 checkpoints...")
    try:
        checkpoints = list(checkpointer.list(config))
        print(f"✅ 找到 {len(checkpoints)} 个 checkpoints")
        for i, cp in enumerate(checkpoints):
            print(f"  - Checkpoint {i+1}: {cp.checkpoint['id']}")
    except Exception as e:
        print(f"❌ 列出 checkpoints 失败: {e}")
    
    # 测试业务功能
    print("\n👤 测试用户会话查询...")
    try:
        user_id = config['configurable']['user_id']
        sessions = checkpointer.get_user_sessions(user_id)
        print(f"✅ 找到用户 {user_id} 的 {len(sessions)} 个会话")
        for session in sessions:
            print(f"  - {session['session_id']}: {session['topic']} ({session['status']})")
    except Exception as e:
        print(f"❌ 用户会话查询失败: {e}")
    
    # 测试会话信息查询
    print("\n📊 测试会话信息查询...")
    try:
        session_id = config['configurable']['session_id']
        session_info = checkpointer.get_session_info(session_id)
        if session_info:
            print("✅ 会话信息查询成功")
            print(f"  - Session ID: {session_info['session_id']}")
            print(f"  - Topic: {session_info['topic']}")
            print(f"  - Status: {session_info['status']}")
            print(f"  - Created: {session_info['created_at']}")
        else:
            print("❌ 会话信息查询失败: 未找到会话")
    except Exception as e:
        print(f"❌ 会话信息查询失败: {e}")
    
    # 测试状态更新
    print("\n🔄 测试会话状态更新...")
    try:
        session_id = config['configurable']['session_id']
        success = checkpointer.update_session_status(session_id, "completed")
        if success:
            print("✅ 会话状态更新成功")
            # 验证更新
            updated_info = checkpointer.get_session_info(session_id)
            if updated_info:
                print(f"  - 新状态: {updated_info['status']}")
        else:
            print("❌ 会话状态更新失败")
    except Exception as e:
        print(f"❌ 会话状态更新失败: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_checkpoint())
