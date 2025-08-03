#!/usr/bin/env python3
"""
Complete Resume Functionality Test
Tests the full interrupt -> user response -> resume flow with streaming
"""

import requests
import json
import time
import sys
import os
import asyncio
from typing import Dict, Any

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# API 基础 URL
BASE_URL = "http://localhost:8000"

class ResumeTestSuite:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        
    def check_service_health(self) -> bool:
        """检查服务健康状态"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False
    
    def create_interactive_task(self, topic: str, user_id: str = "test_user") -> Dict[str, Any]:
        """创建交互式任务"""
        task_config = {
            "config": {
                "topic": topic,
                "mode": "interactive",  # 交互模式，会触发中断
                "max_words": 1000,
                "style": "formal",
                "language": "zh"
            },
            "user_id": user_id
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/tasks", json=task_config)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"创建任务失败: {response.status_code} - {response.text}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        response = self.session.get(f"{self.base_url}/api/v1/tasks/{task_id}")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"获取任务状态失败: {response.status_code} - {response.text}")
    
    def resume_task(self, task_id: str, user_response: Dict[str, Any]) -> Dict[str, Any]:
        """恢复任务"""
        response = self.session.post(f"{self.base_url}/api/v1/tasks/{task_id}/resume", json=user_response)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"恢复任务失败: {response.status_code} - {response.text}")
    
    def wait_for_status_change(self, task_id: str, expected_status: str, timeout: int = 30) -> Dict[str, Any]:
        """等待任务状态变化"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                status = self.get_task_status(task_id)
                current_status = status.get("status")
                
                print(f"   当前状态: {current_status}")
                
                if current_status == expected_status:
                    return status
                elif current_status == "failed":
                    error_msg = status.get("error_message", "未知错误")
                    raise Exception(f"任务执行失败: {error_msg}")
                
                time.sleep(2)
                
            except Exception as e:
                if "404" in str(e):
                    print(f"   任务还未创建状态记录，继续等待...")
                    time.sleep(1)
                else:
                    raise e
        
        raise Exception(f"等待状态变化超时: 期望 {expected_status}")
    
    def test_basic_task_execution(self):
        """测试基本任务执行"""
        print("\n" + "="*60)
        print("🧪 测试 1: 基本任务执行")
        print("="*60)
        
        # 创建自动模式任务（不会中断）
        task_data = self.create_interactive_task("人工智能基础概念", "test_basic")
        task_id = task_data["task_id"]
        
        print(f"✅ 任务创建成功: {task_id}")
        
        # 等待任务完成
        final_status = self.wait_for_status_change(task_id, "completed", timeout=60)
        
        print(f"✅ 任务执行完成")
        print(f"   文章字数: {final_status.get('word_count', 0)}")
        print(f"   生成时间: {final_status.get('generation_time', 0):.2f} 秒")
        
        return True
    
    def test_interrupt_and_resume_flow(self):
        """测试完整的中断和恢复流程"""
        print("\n" + "="*60)
        print("🧪 测试 2: 中断和恢复流程")
        print("="*60)
        
        # 创建交互式任务
        task_data = self.create_interactive_task("区块链技术在金融领域的应用", "test_interrupt")
        task_id = task_data["task_id"]
        
        print(f"✅ 交互式任务创建成功: {task_id}")
        
        # 等待任务执行到中断点
        print("⏳ 等待任务执行到中断点...")
        
        # 检查任务是否被中断
        interrupted = False
        for i in range(30):  # 最多等待60秒
            status = self.get_task_status(task_id)
            current_status = status.get("status")
            current_step = status.get("current_step", "")
            
            print(f"   状态: {current_status}, 步骤: {current_step}")
            
            if current_status == "paused" or "awaiting" in current_step.lower():
                print(f"✅ 任务已中断，等待用户响应")
                interrupted = True
                
                # 显示大纲（如果有）
                outline = status.get("outline")
                if outline:
                    print(f"   生成的大纲:")
                    print(f"     标题: {outline.get('title', 'N/A')}")
                    sections = outline.get("sections", [])
                    for i, section in enumerate(sections[:3], 1):
                        print(f"     {i}. {section.get('title', 'N/A')}")
                
                break
            elif current_status == "completed":
                print(f"⚠️ 任务直接完成，没有触发中断")
                return False
            elif current_status == "failed":
                error_msg = status.get("error_message", "未知错误")
                print(f"❌ 任务执行失败: {error_msg}")
                return False
            
            time.sleep(2)
        
        if not interrupted:
            print(f"❌ 任务未在预期时间内中断")
            return False
        
        # 发送用户响应，恢复任务
        print(f"\n🔄 发送用户响应，恢复任务...")
        
        user_response = {
            "response": "确认继续",
            "approved": True,
            "comment": "大纲看起来不错，请继续写文章"
        }
        
        resume_result = self.resume_task(task_id, user_response)
        print(f"✅ 任务恢复成功: {resume_result.get('message', 'N/A')}")
        
        # 等待任务最终完成
        print(f"⏳ 等待任务最终完成...")
        final_status = self.wait_for_status_change(task_id, "completed", timeout=60)
        
        print(f"🎉 任务完成！")
        print(f"   文章字数: {final_status.get('word_count', 0)}")
        print(f"   生成时间: {final_status.get('generation_time', 0):.2f} 秒")
        
        return True
    
    def test_reject_and_regenerate(self):
        """测试拒绝大纲并重新生成"""
        print("\n" + "="*60)
        print("🧪 测试 3: 拒绝大纲并重新生成")
        print("="*60)
        
        # 创建交互式任务
        task_data = self.create_interactive_task("量子计算的发展前景", "test_reject")
        task_id = task_data["task_id"]
        
        print(f"✅ 交互式任务创建成功: {task_id}")
        
        # 等待中断
        print("⏳ 等待任务中断...")
        time.sleep(10)
        
        # 拒绝大纲
        user_response = {
            "response": "拒绝",
            "approved": False,
            "comment": "大纲不够详细，请重新生成更具体的大纲"
        }
        
        try:
            resume_result = self.resume_task(task_id, user_response)
            print(f"✅ 拒绝响应发送成功: {resume_result.get('message', 'N/A')}")
            return True
        except Exception as e:
            print(f"⚠️ 拒绝测试失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始 Resume 功能完整测试")
        print("="*60)
        
        # 检查服务状态
        if not self.check_service_health():
            print("❌ API 服务未运行，请先启动服务")
            return False
        
        print("✅ API 服务运行正常")
        
        # 运行测试
        tests = [
            ("基本任务执行", self.test_basic_task_execution),
            ("中断和恢复流程", self.test_interrupt_and_resume_flow),
            ("拒绝和重新生成", self.test_reject_and_regenerate)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
                if result:
                    print(f"✅ {test_name}: 通过")
                else:
                    print(f"❌ {test_name}: 失败")
            except Exception as e:
                print(f"❌ {test_name}: 异常 - {e}")
                results.append((test_name, False))
        
        # 总结
        print("\n" + "="*60)
        print("📊 测试结果总结")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {test_name}: {status}")
        
        print(f"\n总计: {passed}/{total} 测试通过")
        
        if passed == total:
            print("🎉 所有测试通过！Resume 功能正常工作")
        else:
            print("⚠️ 部分测试失败，需要进一步调试")
        
        return passed == total

if __name__ == "__main__":
    test_suite = ResumeTestSuite()
    success = test_suite.run_all_tests()
    sys.exit(0 if success else 1)
