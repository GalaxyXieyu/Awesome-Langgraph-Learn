# 测试文件说明

## test_realtime_stream.py

**实时流式输出测试脚本**

### 功能
- 测试简化后的chunk处理效果
- 实时显示流式输出数据
- 验证消息类型转换 (如 `interrupt_request` → `interrupt`)
- 检查数据简化效果

### 使用方法
```bash
# 确保服务已启动
cd backend
conda activate langgraph
python main.py

# 在另一个终端运行测试
cd tests
conda activate langgraph
python -u test_realtime_stream.py
```

### 预期输出
- 实时显示每个chunk
- 简化的消息格式：`message_type | node | content`
- 系统消息和错误处理
- 自动停止在25个chunk

### 验证要点
1. ✅ 双层嵌套解包正常
2. ✅ 消息类型转换正确
3. ✅ 只保留核心字段
4. ✅ 实时流式显示
5. ✅ 中断消息特别标注
