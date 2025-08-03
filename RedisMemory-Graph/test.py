"""
LangGraph Redis 存储测试
"""

import json
import redis
from tools import chat_with_memory


def test_redis_graph():
    """测试 LangGraph Redis 存储"""
    print("🔴 测试 LangGraph Redis 存储")
    print("-" * 40)

    try:
        from graph import create_chat_bot_with_redis
        from langgraph.checkpoint.redis import RedisSaver

        # 获取工作流和 Redis URL
        workflow, redis_url = create_chat_bot_with_redis()
        thread_id = "test_session"

        print(f"🔗 连接 Redis: {redis_url}")

        # 使用官方 Redis 存储
        with RedisSaver.from_conn_string(redis_url) as checkpointer:
            print("✅ RedisSaver 创建成功")

            # 创建索引
            checkpointer.setup()
            print("✅ 索引创建成功")

            # 编译图
            app = workflow.compile(checkpointer=checkpointer)
            print("✅ Graph 编译成功")

            # 测试对话记忆
            response1 = chat_with_memory(app, "我叫小明，我是程序员", thread_id)
            print(f"👤 我叫小明，我是程序员")
            print(f"🤖 {response1}")

            response2 = chat_with_memory(app, "我叫什么名字？我的职业是什么？", thread_id)
            print(f"👤 我叫什么名字？我的职业是什么？")
            print(f"🤖 {response2}")

            # 检查记忆
            success = ("小明" in response2) and ("程序员" in response2 or "编程" in response2)
            print(f"📊 记忆测试: {'✅ 通过' if success else '❌ 失败'}")

            return success

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def view_redis_data(thread_id="test_session"):
    """查看 Redis 中的 LangGraph 数据"""
    print("\n📊 查看 Redis 数据")
    print("-" * 30)

    try:
        redis_url = "redis://default:mfzstl2v@dbconn.sealoshzh.site:41277"
        client = redis.from_url(redis_url)

        # 查找所有相关键
        all_keys = client.keys('*')
        langgraph_keys = [k for k in all_keys if b'checkpoint' in k and thread_id.encode() in k]

        print(f"🔍 找到 {len(langgraph_keys)} 个相关键")

        # 显示前几个键的数据
        for key in langgraph_keys[:3]:
            key_str = key.decode('utf-8')
            print(f"\n🔑 {key_str}")

            try:
                # 使用 RedisJSON 读取
                data = client.execute_command('JSON.GET', key)
                if data:
                    parsed = json.loads(data.decode('utf-8'))
                    print(f"   📝 类型: {parsed.get('type', 'unknown')}")
                    print(f"   📄 通道: {parsed.get('channel', 'unknown')}")

                    # 如果是消息数据
                    if parsed.get('channel') == 'messages' and 'blob' in parsed:
                        try:
                            blob_data = json.loads(parsed['blob'])
                            if isinstance(blob_data, list):
                                print(f"   💬 消息数量: {len(blob_data)}")
                                for i, msg in enumerate(blob_data[:2]):  # 只显示前2条
                                    if isinstance(msg, dict) and 'kwargs' in msg:
                                        content = msg['kwargs'].get('content', '')[:30]
                                        msg_type = msg['kwargs'].get('type', 'unknown')
                                        print(f"      [{i}] {msg_type}: {content}...")
                        except:
                            pass
            except Exception as e:
                print(f"   ❌ 读取失败: {e}")

        print(f"\n📈 统计: 总共 {len(all_keys)} 个键，{len(langgraph_keys)} 个 LangGraph 相关")

    except Exception as e:
        print(f"❌ 查看数据失败: {e}")


if __name__ == "__main__":
    print("🚀 LangGraph Redis 测试")
    print("=" * 40)

    # 测试 Redis Graph
    success = test_redis_graph()

    # 查看 Redis 数据
    if success:
        view_redis_data()

    print(f"\n📊 测试结果: {'✅ 通过' if success else '❌ 失败'}")
    print("✅ 测试完成！")




