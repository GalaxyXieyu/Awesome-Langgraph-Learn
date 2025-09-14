const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));
const EventSource = require('eventsource');

async function testAPIAndStream() {
    try {
        console.log('开始API测试...');
        
        // 1. 创建任务
        const createTaskResponse = await fetch('http://localhost:8000/research/tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                topic: '人工智能发展趋势测试',
                user_id: 'test_user',
                mode: 'interactive'
            })
        });
        
        if (!createTaskResponse.ok) {
            throw new Error(`HTTP error! status: ${createTaskResponse.status}`);
        }
        
        const taskData = await createTaskResponse.json();
        console.log('任务创建成功:', taskData);
        
        // 2. 监听流式数据
        const taskId = taskData.task_id;
        console.log(`开始监听任务 ${taskId} 的流式数据...`);
        
        const eventSource = new EventSource(`http://localhost:8000/research/tasks/${taskId}/stream`);
        let messageCount = 0;
        let jsonMessages = [];
        
        eventSource.onmessage = function(event) {
            messageCount++;
            console.log(`\n=== 消息 ${messageCount} ===`);
            
            try {
                const data = JSON.parse(event.data);
                console.log('消息类型:', data.type);
                
                if (data.data) {
                    const messageData = data.data;
                    console.log('内容类型:', messageData.message_type);
                    console.log('节点:', messageData.node);
                    console.log('内容长度:', messageData.content?.length);
                    
                    // 检查是否包含JSON数据
                    if (messageData.content) {
                        const content = messageData.content.trim();
                        if (content.startsWith('{') || content.startsWith('[')) {
                            console.log('🔍 发现JSON内容:');
                            console.log('前100字符:', content.substring(0, 100));
                            jsonMessages.push({
                                type: messageData.message_type,
                                node: messageData.node,
                                contentLength: content.length,
                                isValidJSON: isValidJSON(content)
                            });
                        }
                    }
                }
            } catch (error) {
                console.log('解析消息失败:', error.message);
                console.log('原始数据:', event.data.substring(0, 200));
            }
        };
        
        eventSource.onerror = function(error) {
            console.log('EventSource 错误:', error);
        };
        
        // 运行30秒后停止
        setTimeout(() => {
            console.log('\n=== 测试结果总结 ===');
            console.log(`总消息数: ${messageCount}`);
            console.log(`JSON消息数: ${jsonMessages.length}`);
            
            if (jsonMessages.length > 0) {
                console.log('\nJSON消息详情:');
                jsonMessages.forEach((msg, index) => {
                    console.log(`${index + 1}. 类型: ${msg.type}, 节点: ${msg.node}, 长度: ${msg.contentLength}, 有效JSON: ${msg.isValidJSON}`);
                });
            }
            
            eventSource.close();
            process.exit(0);
        }, 30000);
        
    } catch (error) {
        console.error('测试失败:', error.message);
        process.exit(1);
    }
}

function isValidJSON(str) {
    try {
        JSON.parse(str);
        return true;
    } catch (e) {
        return false;
    }
}

testAPIAndStream();