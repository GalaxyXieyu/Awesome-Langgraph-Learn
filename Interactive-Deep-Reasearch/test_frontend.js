const puppeteer = require('puppeteer');

async function testFrontendApp() {
    let browser;
    try {
        console.log('启动浏览器...');
        browser = await puppeteer.launch({
            headless: false, // 显示浏览器窗口以便观察
            defaultViewport: { width: 1280, height: 720 }
        });
        
        const page = await browser.newPage();
        
        // 监听控制台消息
        page.on('console', msg => console.log('浏览器控制台:', msg.text()));
        page.on('pageerror', error => console.log('页面错误:', error.message));
        
        console.log('访问前端应用...');
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle0' });
        
        console.log('等待页面加载...');
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // 截取初始页面
        await page.screenshot({ path: 'frontend_initial.png', fullPage: true });
        console.log('已截取初始页面: frontend_initial.png');
        
        // 查找并点击开始生成按钮或输入框
        try {
            // 尝试找到主题输入框
            const topicInput = await page.$('input[placeholder*="主题"], input[placeholder*="topic"], textarea[placeholder*="主题"], textarea[placeholder*="topic"]');
            if (topicInput) {
                console.log('找到主题输入框，输入测试主题...');
                await topicInput.click();
                await topicInput.type('人工智能发展趋势');
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
            
            // 尝试找到开始生成按钮
            const generateButton = await page.$('button:not([disabled])');
            if (generateButton) {
                const buttonText = await page.evaluate(el => el.textContent, generateButton);
                console.log('找到按钮:', buttonText);
                
                if (buttonText.includes('生成') || buttonText.includes('开始') || buttonText.includes('Start')) {
                    console.log('点击生成按钮...');
                    await generateButton.click();
                    
                    // 等待消息开始出现
                    console.log('等待消息流开始...');
                    await new Promise(resolve => setTimeout(resolve, 5000));
                    
                    // 截取生成过程中的页面
                    await page.screenshot({ path: 'frontend_generating.png', fullPage: true });
                    console.log('已截取生成过程页面: frontend_generating.png');
                    
                    // 等待更多消息
                    await new Promise(resolve => setTimeout(resolve, 10000));
                    
                    // 截取最终状态
                    await page.screenshot({ path: 'frontend_final.png', fullPage: true });
                    console.log('已截取最终页面: frontend_final.png');
                    
                    // 检查页面中的JSON消息显示情况
                    const jsonElements = await page.$$('.json-content, .code-content, pre');
                    console.log(`找到 ${jsonElements.length} 个JSON/代码内容元素`);
                    
                    // 获取页面中的所有消息内容
                    const messages = await page.evaluate(() => {
                        const messageElements = document.querySelectorAll('.message-content, [class*="message"], [class*="content"]');
                        return Array.from(messageElements).slice(0, 10).map(el => ({
                            className: el.className,
                            textContent: el.textContent?.substring(0, 200) + '...'
                        }));
                    });
                    
                    console.log('页面消息样本:', JSON.stringify(messages, null, 2));
                }
            }
            
        } catch (error) {
            console.log('测试过程中的错误:', error.message);
        }
        
        // 保持页面打开一段时间以便观察
        console.log('保持页面打开30秒以便观察...');
        await new Promise(resolve => setTimeout(resolve, 30000));
        
    } catch (error) {
        console.error('测试失败:', error);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

testFrontendApp();