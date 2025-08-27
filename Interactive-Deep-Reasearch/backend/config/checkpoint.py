"""自定义 PostgreSQL Checkpoint Saver"""
import json
import time
from typing import Dict, Any, Optional, Iterator, List
import psycopg
from psycopg.rows import dict_row
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from .database import get_database_url, get_connection_kwargs


class ResearchPostgresSaver(BaseCheckpointSaver):
    """研究系统专用的 PostgreSQL Checkpoint Saver"""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        初始化 checkpoint saver
        
        Args:
            connection_string: 数据库连接字符串，如果为空则使用默认配置
        """
        self.connection_string = connection_string or get_database_url()
        self.serializer = JsonPlusSerializer()
        print(f"🔗 初始化 ResearchPostgresSaver: {self._mask_connection_string()}")
        
    def _mask_connection_string(self) -> str:
        """隐藏连接字符串中的敏感信息"""
        if "://" in self.connection_string:
            parts = self.connection_string.split("://")
            if len(parts) == 2:
                protocol = parts[0]
                rest = parts[1]
                if "@" in rest:
                    auth_part, host_part = rest.split("@", 1)
                    if ":" in auth_part:
                        user, _ = auth_part.split(":", 1)
                        return f"{protocol}://{user}:***@{host_part}"
        return self.connection_string

    def _deserialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        反序列化存储的数据

        Args:
            data: 从数据库读取的数据

        Returns:
            反序列化后的数据
        """
        try:
            if isinstance(data, dict) and data.get("type") == "jsonplus_serialized":
                # 这是用 JsonPlusSerializer 序列化的数据
                import base64
                encoded_data = data["data"]
                decoded_bytes = base64.b64decode(encoded_data.encode('utf-8'))
                return self.serializer.loads(decoded_bytes)
            else:
                # 直接返回原始数据（向后兼容）
                return data
        except Exception as e:
            print(f"⚠️  反序列化数据失败，返回原始数据: {e}")
            return data
        
    def setup(self):
        """创建表结构"""
        print("🏗️  开始创建数据库表结构...")
        
        try:
            with psycopg.connect(self.connection_string, **get_connection_kwargs()) as conn:
                with conn.cursor() as cur:
                    # 创建会话表
                    print("📋 创建 research_sessions 表...")
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS research_sessions (
                            session_id VARCHAR(255) PRIMARY KEY,
                            user_id VARCHAR(100) NOT NULL,
                            topic TEXT NOT NULL,
                            status VARCHAR(20) DEFAULT 'pending',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    
                    # 创建 checkpoint 表
                    print("🔄 创建 research_checkpoints 表...")
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS research_checkpoints (
                            thread_id VARCHAR(255) NOT NULL,
                            thread_ts VARCHAR(255) NOT NULL,
                            parent_ts VARCHAR(255),
                            checkpoint JSONB,
                            metadata JSONB,
                            
                            session_id VARCHAR(255),
                            user_id VARCHAR(100),
                            task_type VARCHAR(50),
                            
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            
                            PRIMARY KEY (thread_id, thread_ts)
                        );
                    """)
                    
                    # 创建索引
                    print("📊 创建索引...")
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_session_checkpoints 
                        ON research_checkpoints (session_id, created_at);
                    """)
                    
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_user_checkpoints 
                        ON research_checkpoints (user_id, created_at);
                    """)
                    
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_user_sessions 
                        ON research_sessions (user_id, created_at);
                    """)
                    
                    print("✅ 数据库表创建成功")
                    
        except Exception as e:
            print(f"❌ 创建数据库表失败: {e}")
            raise
    
    def put(self, config: RunnableConfig, checkpoint: Dict[str, Any], 
            metadata: Dict[str, Any], new_versions: Dict[str, Any]) -> RunnableConfig:
        """
        存储 checkpoint
        
        Args:
            config: 运行配置
            checkpoint: checkpoint 数据
            metadata: 元数据
            new_versions: 新版本信息
            
        Returns:
            更新后的配置
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        
        # 序列化数据 - 使用 JsonPlusSerializer 处理复杂对象，然后转换为 JSON 字符串
        try:
            import json
            # 先用 JsonPlusSerializer 序列化，然后解码为字符串存储到 JSONB
            checkpoint_bytes = self.serializer.dumps(checkpoint)
            metadata_bytes = self.serializer.dumps(metadata)

            # 将字节数据转换为 base64 字符串，以便存储在 JSONB 中
            import base64
            serialized_checkpoint = json.dumps({
                "data": base64.b64encode(checkpoint_bytes).decode('utf-8'),
                "type": "jsonplus_serialized"
            })
            serialized_metadata = json.dumps({
                "data": base64.b64encode(metadata_bytes).decode('utf-8'),
                "type": "jsonplus_serialized"
            })
        except Exception as e:
            print(f"❌ 序列化数据失败: {e}")
            raise
        
        # 提取业务字段
        session_id = config["configurable"].get("session_id", thread_id)
        user_id = config["configurable"].get("user_id", "unknown")
        task_type = config["configurable"].get("task_type", "research")
        
        try:
            with psycopg.connect(self.connection_string, **get_connection_kwargs()) as conn:
                with conn.cursor() as cur:
                    # 插入或更新 checkpoint
                    cur.execute("""
                        INSERT INTO research_checkpoints 
                        (thread_id, thread_ts, parent_ts, checkpoint, metadata, 
                         session_id, user_id, task_type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (thread_id, thread_ts) 
                        DO UPDATE SET 
                            checkpoint = EXCLUDED.checkpoint,
                            metadata = EXCLUDED.metadata,
                            session_id = EXCLUDED.session_id,
                            user_id = EXCLUDED.user_id,
                            task_type = EXCLUDED.task_type
                    """, (
                        thread_id,
                        checkpoint["ts"],
                        checkpoint.get("parent_ts"),
                        serialized_checkpoint,
                        serialized_metadata,
                        session_id,
                        user_id,
                        task_type
                    ))
                    
                    # 更新或创建会话记录
                    self._upsert_session(cur, session_id, user_id, config)
                    
        except Exception as e:
            print(f"❌ 存储 checkpoint 失败: {e}")
            raise
        
        return config

    def _upsert_session(self, cursor, session_id: str, user_id: str, config: RunnableConfig):
        """
        更新或创建会话记录

        Args:
            cursor: 数据库游标
            session_id: 会话ID
            user_id: 用户ID
            config: 运行配置
        """
        # 从 config 或其他地方提取 topic
        topic = config["configurable"].get("topic", "未知主题")

        cursor.execute("""
            INSERT INTO research_sessions (session_id, user_id, topic, status, updated_at)
            VALUES (%s, %s, %s, 'in_progress', CURRENT_TIMESTAMP)
            ON CONFLICT (session_id)
            DO UPDATE SET
                status = 'in_progress',
                updated_at = CURRENT_TIMESTAMP
        """, (session_id, user_id, topic))

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """
        获取 checkpoint

        Args:
            config: 运行配置

        Returns:
            CheckpointTuple 或 None
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"].get("checkpoint_id")

        try:
            with psycopg.connect(self.connection_string, **get_connection_kwargs()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    if checkpoint_id:
                        # 获取特定 checkpoint
                        cur.execute("""
                            SELECT * FROM research_checkpoints
                            WHERE thread_id = %s AND thread_ts = %s
                        """, (thread_id, checkpoint_id))
                    else:
                        # 获取最新 checkpoint
                        cur.execute("""
                            SELECT * FROM research_checkpoints
                            WHERE thread_id = %s
                            ORDER BY created_at DESC
                            LIMIT 1
                        """, (thread_id,))

                    row = cur.fetchone()
                    if not row:
                        return None

                    # 反序列化数据 - 从 base64 编码的 JsonPlusSerializer 数据恢复
                    checkpoint = self._deserialize_data(row["checkpoint"]) if row["checkpoint"] else {}
                    metadata = self._deserialize_data(row["metadata"]) if row["metadata"] else {}

                    return CheckpointTuple(
                        config={
                            "configurable": {
                                "thread_id": row["thread_id"],
                                "checkpoint_ns": "",
                                "checkpoint_id": row["thread_ts"]
                            }
                        },
                        checkpoint=checkpoint,
                        metadata=metadata,
                        parent_config=None,  # 简化版本暂不处理
                        pending_writes=[]
                    )

        except Exception as e:
            print(f"❌ 获取 checkpoint 失败: {e}")
            return None

    def list(self, config: RunnableConfig) -> Iterator[CheckpointTuple]:
        """
        列出 checkpoints

        Args:
            config: 运行配置

        Yields:
            CheckpointTuple 迭代器
        """
        thread_id = config["configurable"]["thread_id"]

        try:
            with psycopg.connect(self.connection_string, **get_connection_kwargs()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("""
                        SELECT * FROM research_checkpoints
                        WHERE thread_id = %s
                        ORDER BY created_at DESC
                    """, (thread_id,))

                    for row in cur.fetchall():
                        try:
                            # 反序列化数据
                            checkpoint = self._deserialize_data(row["checkpoint"]) if row["checkpoint"] else {}
                            metadata = self._deserialize_data(row["metadata"]) if row["metadata"] else {}

                            yield CheckpointTuple(
                                config={
                                    "configurable": {
                                        "thread_id": row["thread_id"],
                                        "checkpoint_ns": "",
                                        "checkpoint_id": row["thread_ts"]
                                    }
                                },
                                checkpoint=checkpoint,
                                metadata=metadata,
                                parent_config=None,
                                pending_writes=[]
                            )
                        except Exception as e:
                            print(f"⚠️  跳过损坏的 checkpoint {row['thread_ts']}: {e}")
                            continue

        except Exception as e:
            print(f"❌ 列出 checkpoints 失败: {e}")
            return

    # ========================================================================
    # 业务功能方法
    # ========================================================================

    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取用户的会话列表（业务功能）

        Args:
            user_id: 用户ID
            limit: 返回数量限制

        Returns:
            会话列表
        """
        try:
            with psycopg.connect(self.connection_string, **get_connection_kwargs()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("""
                        SELECT * FROM research_sessions
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (user_id, limit))

                    return cur.fetchall()

        except Exception as e:
            print(f"❌ 获取用户会话失败: {e}")
            return []

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话详细信息

        Args:
            session_id: 会话ID

        Returns:
            会话信息字典或 None
        """
        try:
            with psycopg.connect(self.connection_string, **get_connection_kwargs()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("""
                        SELECT * FROM research_sessions
                        WHERE session_id = %s
                    """, (session_id,))

                    return cur.fetchone()

        except Exception as e:
            print(f"❌ 获取会话信息失败: {e}")
            return None

    def update_session_status(self, session_id: str, status: str) -> bool:
        """
        更新会话状态

        Args:
            session_id: 会话ID
            status: 新状态

        Returns:
            是否更新成功
        """
        try:
            with psycopg.connect(self.connection_string, **get_connection_kwargs()) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE research_sessions
                        SET status = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE session_id = %s
                    """, (status, session_id))

                    return cur.rowcount > 0

        except Exception as e:
            print(f"❌ 更新会话状态失败: {e}")
            return False

    def cleanup_old_checkpoints(self, days: int = 7) -> int:
        """
        清理旧的 checkpoints

        Args:
            days: 保留天数

        Returns:
            清理的记录数
        """
        try:
            with psycopg.connect(self.connection_string, **get_connection_kwargs()) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM research_checkpoints
                        WHERE created_at < NOW() - INTERVAL '%s days'
                    """, (days,))

                    deleted_count = cur.rowcount
                    print(f"🧹 清理了 {deleted_count} 个过期的 checkpoints")
                    return deleted_count

        except Exception as e:
            print(f"❌ 清理 checkpoints 失败: {e}")
            return 0

    # ========================================================================
    # 异步方法实现 (LangGraph 需要)
    # ========================================================================

    async def aput(self, config: RunnableConfig, checkpoint: Dict[str, Any],
                   metadata: Dict[str, Any], new_versions: Dict[str, Any]) -> RunnableConfig:
        """异步存储 checkpoint"""
        return self.put(config, checkpoint, metadata, new_versions)

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """异步获取 checkpoint"""
        return self.get_tuple(config)

    async def alist(self, config: RunnableConfig) -> Iterator[CheckpointTuple]:
        """异步列出 checkpoints"""
        for item in self.list(config):
            yield item
