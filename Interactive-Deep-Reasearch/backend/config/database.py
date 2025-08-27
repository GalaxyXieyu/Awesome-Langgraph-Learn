"""数据库配置模块"""
import os
from typing import Optional, Dict, Any

def get_database_url() -> str:
    """
    获取数据库连接URL

    优先使用 PG_URL 环境变量，如果没有则使用单独的配置项构建

    Returns:
        PostgreSQL 连接字符串
    """
    # 优先使用完整的 PG_URL
    pg_url = os.environ.get("PG_URL")
    if pg_url:
        return pg_url

    # 如果没有 PG_URL，则使用单独的配置项构建
    config = {
        "host": os.environ.get("PG_HOST", "localhost"),
        "port": int(os.environ.get("PG_PORT", "5432")),
        "database": os.environ.get("PG_DATABASE", "agents"),
        "user": os.environ.get("PG_USER", "user"),
        "password": os.environ.get("PG_PASSWORD", "password"),
        "sslmode": os.environ.get("PG_SSLMODE", "prefer"),
    }

    return (
        f"postgresql://{config['user']}:{config['password']}"
        f"@{config['host']}:{config['port']}/{config['database']}"
        f"?sslmode={config['sslmode']}"
    )

# 为了兼容性，保留 DATABASE_CONFIG
DATABASE_CONFIG = {
    "url": get_database_url(),
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": int(os.environ.get("PG_PORT", "5432")),
    "database": os.environ.get("PG_DATABASE", "agents"),
    "user": os.environ.get("PG_USER", "user"),
    "password": os.environ.get("PG_PASSWORD", "password"),
    "sslmode": os.environ.get("PG_SSLMODE", "prefer"),
}

def get_connection_kwargs() -> Dict[str, Any]:
    """
    获取 psycopg 连接参数
    
    Returns:
        psycopg 连接参数字典
    """
    return {
        "autocommit": True,
        # 注意：这里不能直接传 "dict_row"，需要在连接时设置
    }

def validate_database_config() -> Dict[str, Any]:
    """
    验证数据库配置
    
    Returns:
        验证结果字典
    """
    result = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    
    # 检查必要的配置项
    required_fields = ["host", "port", "database", "user"]
    for field in required_fields:
        if not DATABASE_CONFIG.get(field):
            result["is_valid"] = False
            result["errors"].append(f"缺少必要的数据库配置: {field}")
    
    # 检查端口号
    try:
        port = int(DATABASE_CONFIG["port"])
        if port <= 0 or port > 65535:
            result["warnings"].append("端口号应该在 1-65535 范围内")
    except (ValueError, TypeError):
        result["is_valid"] = False
        result["errors"].append("端口号必须是有效的整数")
    
    # 检查密码
    if not DATABASE_CONFIG.get("password"):
        result["warnings"].append("数据库密码为空，请确保这是预期的配置")
    
    return result

def print_database_config():
    """打印数据库配置信息（隐藏敏感信息）"""
    config = DATABASE_CONFIG.copy()
    if config.get("password"):
        config["password"] = "*" * len(config["password"])
    
    print("📊 数据库配置:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    # 验证配置
    validation = validate_database_config()
    if validation["is_valid"]:
        print("✅ 配置验证通过")
    else:
        print("❌ 配置验证失败:")
        for error in validation["errors"]:
            print(f"  - {error}")
    
    if validation["warnings"]:
        print("⚠️  配置警告:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")

if __name__ == "__main__":
    print_database_config()
