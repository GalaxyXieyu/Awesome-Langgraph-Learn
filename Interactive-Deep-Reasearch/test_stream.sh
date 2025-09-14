#!/bin/bash

echo "🧪 开始测试流式数据..."
echo "📡 监听任务 eb6bb1f0 的数据流..."

# 使用 curl 监听服务器发送的事件流
timeout 30s curl -N -H "Accept: text/event-stream" \
    "http://localhost:8000/research/tasks/eb6bb1f0/stream" \
    2>/dev/null | while IFS= read -r line; do
    
    # 跳过空行和连接信息
    if [[ -z "$line" ]]; then
        continue
    fi
    
    # 提取data:开头的行
    if [[ $line == data:* ]]; then
        data="${line#data: }"
        
        # 尝试解析JSON
        if echo "$data" | jq . >/dev/null 2>&1; then
            echo "📋 消息数据:"
            echo "$data" | jq -C .
            
            # 检查是否包含JSON内容
            content_type=$(echo "$data" | jq -r '.data.message_type // .type // "unknown"' 2>/dev/null)
            content=$(echo "$data" | jq -r '.data.content // .content // ""' 2>/dev/null)
            
            if [[ $content == {* ]] || [[ $content == [* ]]; then
                echo "🔍 发现JSON内容片段 (类型: $content_type):"
                echo "$content" | head -c 200
                echo ""
                if echo "$content" | jq . >/dev/null 2>&1; then
                    echo "✅ 完整有效的JSON数据"
                else
                    echo "⚠️  不完整的JSON片段"
                fi
            fi
            
            echo "---"
        else
            echo "⚠️  非JSON数据: $data"
        fi
    fi
done

echo "🏁 测试完成"