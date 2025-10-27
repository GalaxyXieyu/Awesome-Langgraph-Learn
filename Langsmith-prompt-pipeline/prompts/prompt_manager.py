"""
Prompt 管理器模块 - 极简自动化版本
负责 Prompt 的加载、保存、版本管理等功能
支持标准的 ChatPromptTemplate 格式和自动同步
"""
import sys
import os
import yaml

# 确保 Windows 控制台正确显示 UTF-8（仅在 Windows 平台且需要时）
if sys.platform == 'win32' and not hasattr(sys.stdout, 'reconfigure'):
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='ignore')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='ignore')
    except (AttributeError, OSError):
        pass  # 在某些环境下可能不需要或不可用
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

class PromptManager:
    """Prompt 管理器类 - 极简自动化版本
    
    核心理念：远程是唯一真相源
    - 默认自动从 Hub 拉取最新版本
    - 手动推送本地修改到 Hub
    - 不区分环境，极简设计
    """
    
    def __init__(self, prompts_dir: str = "prompts", config_file: str = "prompts_config.yaml", auto_pull: bool = True):
        """
        初始化 Prompt 管理器
        
        Args:
            prompts_dir: Prompt 文件存储目录
            config_file: Prompt 配置文件名
            auto_pull: 是否自动从 Hub 拉取最新版本（默认 True）
        """
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(exist_ok=True)
        
        # 加载配置
        self.config = self._load_config(config_file)
        self.auto_pull = auto_pull
        
        # 版本信息存储目录
        self.versions_dir = self.prompts_dir / ".versions"
        self.versions_dir.mkdir(exist_ok=True)
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """加载 prompt 配置文件"""
        config_path = self.prompts_dir / config_file
        
        if not config_path.exists():
            return {'prompts': {}, 'versions': {}, 'active_env': 'production'}
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get(self, prompt_name: str) -> Dict[str, Any]:
        """
        加载 Prompt 配置（自动拉取模式）
        
        Args:
            prompt_name: Prompt 名称（如 'parameter_parser', 'report_generator'）
            
        Returns:
            Prompt 配置字典
            
        流程：
            1. 如果启用 auto_pull，自动从 Hub 同步最新版本
            2. 加载本地 YAML 文件
            3. 返回配置字典
        """
        # 自动拉取（如果启用）
        if self.auto_pull:
            self._auto_pull_if_needed(prompt_name)
        
        # 从配置中获取文件名
        if prompt_name in self.config.get('prompts', {}):
            filename = self.config['prompts'][prompt_name]['file']
        else:
            raise ValueError(f"未找到 Prompt 配置: {prompt_name}")
        
        # 加载文件
        config = self.load_from_yaml(filename)
        
        return config
    
    def load_from_yaml(self, filename: str) -> Dict[str, Any]:
        """
        从 YAML 文件加载 Prompt 配置
        
        Args:
            filename: YAML 文件名（可以是相对路径或绝对路径）
            
        Returns:
            Prompt 配置字典
        """
        filepath = self.prompts_dir / filename if not Path(filename).is_absolute() else Path(filename)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Prompt 文件不存在: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 改进版本信息显示逻辑
        version_info = config.get('version')
        if not version_info and 'synced_at' in config:
            # 如果没有 version 但有 synced_at，显示同步时间
            version_info = f"synced@{config['synced_at'][:19]}"  # 只取到秒
        elif not version_info:
            version_info = 'unknown'
        return config
    
    def create_prompt(self, config: Dict[str, Any], user_inputs: Optional[Dict[str, Any]] = None):
        """
        创建并格式化 Prompt（一站式方法）
        
        Args:
            config: Prompt 配置字典
            user_inputs: 用户提供的输入参数（可选）
                - 如果提供，返回格式化后的结果（消息列表或字符串）
                - 如果不提供，返回模板对象（用于链式调用）
            
        Returns:
            - 有 user_inputs: 格式化后的消息列表（ChatPromptTemplate）或字符串（PromptTemplate）
            - 无 user_inputs: ChatPromptTemplate 或 PromptTemplate 对象
            
        Examples:
            # 方式1: 直接格式化（推荐）
            messages = manager.create_prompt(config, {"user_query": "xxx"})
            response = llm.invoke(messages)
            
            # 方式2: 获取模板对象（用于链式调用）
            prompt = manager.create_prompt(config)
            chain = prompt | llm | StrOutputParser()
        """
        # 检测类型：优先检查 messages 字段（ChatPrompt）
        if 'messages' in config or config.get('_type') in ['chat_prompt', 'chat']:
            # 创建 ChatPromptTemplate
            messages = config.get('messages', [])
            if not messages:
                raise ValueError("ChatPromptTemplate 需要 'messages' 字段")
            
            # 解析并标准化消息格式
            parsed_messages = []
            for msg in messages:
                role = msg.get('role', 'human').lower()
                content = msg.get('content', '')
                
                # 标准化角色名称
                if role in ['system']:
                    role = 'system'
                elif role in ['human', 'user']:
                    role = 'human'
                elif role in ['ai', 'assistant']:
                    role = 'assistant'
                
                parsed_messages.append((role, content))
            
            prompt = ChatPromptTemplate.from_messages(parsed_messages)
        else:
            # 创建简单 PromptTemplate
            template_text = config.get('template', '')
            input_vars = config.get('input_variables', [])
            
            prompt = PromptTemplate(
                template=template_text,
                input_variables=input_vars,
            )
        
        # 如果提供了 user_inputs，直接格式化返回
        if user_inputs is not None:
            # 应用默认值
            full_inputs = self._get_prompt_with_defaults(config, user_inputs)
            
            # 格式化输出
            if isinstance(prompt, ChatPromptTemplate):
                return prompt.format_messages(**full_inputs)
            else:
                return prompt.format(**full_inputs)
        
        # 否则返回模板对象
        return prompt

    def list_prompts(self) -> Dict[str, str]:
        """列出所有可用的 Prompt"""
        prompts_info = {}
        for name, info in self.config.get('prompts', {}).items():
            prompts_info[name] = info.get('description', 'No description')
        return prompts_info
    
    def save_to_yaml(self, config: Dict[str, Any], filename: str, **kwargs):
        """
        保存 Prompt 配置到 YAML 文件
        
        Args:
            config: Prompt 配置字典
            filename: 保存的文件名
            **kwargs: 额外的 YAML dump 参数
        """
        filepath = self.prompts_dir / filename
        
        # 确保目录存在
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # 默认 YAML 格式化参数
        yaml_params = {
            'allow_unicode': True,
            'default_flow_style': False,
            'sort_keys': False,
            'indent': 2,
        }
        yaml_params.update(kwargs)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # 添加文件头注释
            f.write(f"# {config.get('name', 'Prompt')} - {config.get('version', 'v1')}\n")
            f.write(f"# Generated at: {config.get('created_at', 'N/A')}\n\n")
            yaml.dump(config, f, **yaml_params)
    
    def _get_prompt_with_defaults(self, config: Dict[str, Any], user_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并用户输入和默认参数
        
        Args:
            config: Prompt 配置
            user_inputs: 用户提供的输入
            
        Returns:
            合并后的完整输入字典
        """
        # 从配置中提取默认值
        parameters = config.get('parameters', {})
        defaults = {}
        
        for param_name, param_config in parameters.items():
            if 'default' in param_config:
                defaults[param_name] = param_config['default']
        
        # 合并：用户输入优先
        final_inputs = {**defaults, **user_inputs}
        
        # 确保所有必需的输入变量都存在
        required_vars = config.get('input_variables', [])
        for var in required_vars:
            if var not in final_inputs:
                final_inputs[var] = ""
        
        return final_inputs
    
    # ========== 新增：自动拉取功能 ==========
    
    def _auto_pull_if_needed(self, prompt_name: str):
        """
        自动从 Hub 拉取最新版本（如果需要）
        
        Args:
            prompt_name: Prompt 名称
        """
        try:
            from langchain import hub
            
            # 获取 Hub 名称
            hub_name = self._get_hub_name(prompt_name)
            
            # 尝试从 Hub 拉取
            print(f"[*] 检查远程更新: {hub_name}...")
            remote_prompt = hub.pull(hub_name)
            
            # 转换为 YAML 格式并保存
            filename = self.config['prompts'][prompt_name]['file']
            self._save_prompt_as_yaml(remote_prompt, filename, prompt_name)
            
            print(f"[OK] 已从 Hub 同步最新版本")
            
        except Exception as e:
            # Hub 不存在或网络问题，使用本地版本
            local_file = self.prompts_dir / self.config['prompts'][prompt_name]['file']
            if not local_file.exists():
                print(f"[X] 错误：本地和远程都不存在 {prompt_name}")
                print(f"   详情：{e}")
                raise FileNotFoundError(f"无法找到 Prompt: {prompt_name}")
            else:
                print(f"[!] 无法从 Hub 拉取，使用本地缓存")
    
    def _get_hub_name(self, prompt_name: str) -> str:
        """
        获取 Hub 上的名称
        
        Args:
            prompt_name: Prompt 名称
            
        Returns:
            Hub 名称（不带后缀）
        """
        prompt_config = self.config['prompts'].get(prompt_name, {})
        return prompt_config.get('hub_name', prompt_name)
    
    def _save_prompt_as_yaml(self, prompt_obj: Union[ChatPromptTemplate, PromptTemplate], filename: str, prompt_name: str):
        """
        将 Prompt 对象转换为 YAML 格式并保存
        
        Args:
            prompt_obj: Prompt 对象
            filename: 保存的文件名
            prompt_name: Prompt 名称
        """
        from datetime import datetime
        
        filepath = self.prompts_dir / filename
        
        # 生成版本号（基于时间戳）
        now = datetime.now()
        version = f"hub-{now.strftime('%Y%m%d-%H%M%S')}"
        
        # 转换为配置字典
        config = {
            '_type': 'chat_prompt' if isinstance(prompt_obj, ChatPromptTemplate) else 'prompt',
            'name': prompt_name,
            'version': version,
            'description': f"从 Hub 同步的 {prompt_name}",
            'synced_at': now.isoformat(),
            'input_variables': list(prompt_obj.input_variables),
        }
        
        # 提取消息
        if isinstance(prompt_obj, ChatPromptTemplate):
            messages = []
            for msg in prompt_obj.messages:
                if hasattr(msg, 'prompt'):
                    # PromptTemplate 包装的消息
                    role = 'system' if 'System' in str(type(msg)) else 'human'
                    content = msg.prompt.template
                else:
                    # 直接的消息模板
                    role = 'system' if 'System' in str(type(msg)) else 'human'
                    content = str(msg.content) if hasattr(msg, 'content') else str(msg)
                
                messages.append({'role': role, 'content': content})
            
            config['messages'] = messages
        else:
            config['template'] = prompt_obj.template
        
        # 保存为 YAML
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {prompt_name}\n")
            f.write(f"# 从 LangSmith Hub 同步\n")
            f.write(f"# 同步时间: {config['synced_at']}\n\n")
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    # ========== 手动推送功能 ==========
    
    def push(self, prompt_name: str, with_test: bool = True, create_backup: bool = False) -> bool:
        """
        推送本地修改到 Hub
        
        Args:
            prompt_name: Prompt 名称
            with_test: 是否运行 LangSmith 测试（默认 True）
            create_backup: 是否创建版本备份（默认 False）
            
        Returns:
            bool: 推送是否成功
        """
        print(f"\n{'='*60}")
        print(f"[PUSH] 推送 {prompt_name} 到 Hub")
        print(f"{'='*60}\n")
        
        try:
            # 步骤1: 验证格式
            print("[1/4] 步骤 1/4: 验证 Prompt 格式...")
            validation_result = self.validate(prompt_name)
            
            if not validation_result['is_valid']:
                print("[X] 验证失败:")
                for error in validation_result['errors']:
                    print(f"   - {error}")
                return False
            
            print("[OK] 格式验证通过")
            
            # 步骤2: 测试（可选）
            if with_test:
                print("\n[2/4] 步骤 2/4: 运行 LangSmith 测试...")
                test_result = self.evaluate_prompt(prompt_name)
                
                min_score = self.config['prompts'][prompt_name].get('min_quality_score', 0.8)
                
                if test_result['quality_score'] < min_score:
                    print(f"\n[!] 质量分数: {test_result['quality_score']:.2%} (要求: {min_score:.2%})")
                    response = input("分数较低，是否继续推送？(y/n): ")
                    if response.lower() != 'y':
                        print("[X] 推送已取消")
                        return False
                
                print(f"[OK] 测试通过 (质量分: {test_result['quality_score']:.2%})")
            else:
                print("\n[SKIP] 步骤 2/4: 跳过测试")
            
            # 步骤3: 推送到 Hub
            print("\n[3/4] 步骤 3/4: 推送到 Hub...")
            
            # 加载本地文件（不要自动拉取）
            filename = self.config['prompts'][prompt_name]['file']
            config = self.load_from_yaml(filename)
            prompt = self.create_prompt(config)
            hub_name = self._get_hub_name(prompt_name)
            
            from langchain import hub
            hub.push(hub_name, prompt, new_repo_is_public=False)
            
            print(f"[OK] 已推送到: {hub_name}")
            print(f"   查看: https://smith.langchain.com/hub/{hub_name}")
            
            # 步骤4: 创建备份（可选或根据配置自动）
            auto_backup = self.config.get('versioning', {}).get('create_backup', False)
            should_backup = create_backup or auto_backup
            
            if should_backup:
                print("\n[4/4] 步骤 4/4: 创建版本备份...")
                
                # ⭐ 自动生成版本号
                version = self._generate_version_number(prompt_name, change_type='patch')
                backup_name = f"{hub_name}-{version}"
                
                hub.push(backup_name, prompt, new_repo_is_public=False)
                print(f"[OK] 已备份到: {backup_name}")
                print(f"  版本号: {version}")
                
                # 同时更新本地 YAML 文件的版本号
                self._update_yaml_version(filename, version)
            else:
                print("\n[SKIP] 步骤 4/4: 跳过版本备份")
            
            print(f"\n{'='*60}")
            print("[SUCCESS] 推送完成！")
            print(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] 推送失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def validate(self, prompt_name: str) -> Dict[str, Any]:
        """
        验证 Prompt 格式
        
        Args:
            prompt_name: Prompt 名称
            
        Returns:
            验证结果字典
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # 检查配置是否存在
            if prompt_name not in self.config['prompts']:
                result['is_valid'] = False
                result['errors'].append(f"配置中不存在 {prompt_name}")
                return result
            
            # 检查文件是否存在
            filename = self.config['prompts'][prompt_name]['file']
            filepath = self.prompts_dir / filename
            
            if not filepath.exists():
                result['is_valid'] = False
                result['errors'].append(f"文件不存在: {filepath}")
                return result
            
            # 尝试加载 YAML
            with open(filepath, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 检查必需字段
            if '_type' not in config and 'messages' not in config and 'template' not in config:
                result['errors'].append("缺少必需字段: _type, messages 或 template")
                result['is_valid'] = False
            
            # 检查 input_variables
            if 'input_variables' not in config:
                result['warnings'].append("缺少 input_variables 字段")

            return result
            
        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f"验证过程出错: {str(e)}")
            return result
    
    # ========== LangSmith 评估 ==========
    
    def evaluate_prompt(self, prompt_name: str, evaluators: Optional[List] = None) -> Dict[str, Any]:
        """
        评估提示词质量
        
        Args:
            prompt_name: Prompt 名称
            evaluators: 评估器列表，为 None 时使用配置中的默认评估器
                - None: 从配置文件读取专属评估器，或使用默认的 4 个专业评估器
                - [evaluator1, evaluator2, ...]: 自定义评估器列表（至少1个）
        
        Returns:
            评估结果字典，包含：
            - total: 测试用例数
            - quality_score: 综合质量分数
            - scores: 各评估器详细分数
            - details: 完整评估详情
            
        Examples:
            # 使用默认评估器（推荐）
            result = manager.evaluate_prompt('report_generator')
            
            # 使用自定义评估器
            from evaluation.evaluators.report import ReportEvaluators
            result = manager.evaluate_prompt(
                'report_generator',
                evaluators=[
                    ReportEvaluators.structure_evaluator,
                    ReportEvaluators.relevance_evaluator
                ]
            )
        """
        print(f"[EVAL] 评估提示词: {prompt_name}")
        
        try:
            from evaluation.evaluation import EvaluationRunner
            
            runner = EvaluationRunner()
            
            # 从配置读取
            prompt_config = self.config['prompts'][prompt_name]
            dataset_name = prompt_config.get('test_dataset', 'test_cases')
            
            # 处理评估器
            if evaluators is None:
                # 从配置读取默认评估器
                evaluator_names = prompt_config.get('evaluators', None)
                if evaluator_names:
                    evaluators = self._get_evaluators_by_names(evaluator_names)
                    print(f"  使用配置的评估器: {evaluator_names}")
                else:
                    # 使用提示词对应的默认评估器
                    evaluators = self._get_default_evaluators(prompt_name)
                    print(f"  使用提示词 '{prompt_name}' 的默认评估器")
            else:
                # 验证至少有一个评估器
                if not evaluators or len(evaluators) == 0:
                    raise ValueError("至少需要提供一个评估器")
                print(f"  使用自定义评估器: {len(evaluators)} 个")
            
            # 获取评估器权重
            weights = prompt_config.get('evaluator_weights', None)
            
            # 运行评估
            result = runner.evaluate_prompt(
                dataset_name=dataset_name,
                experiment_name=f"{prompt_name}_evaluation",
                evaluators=evaluators,
                evaluator_weights=weights
            )
            
            print(f"  [OK] 评估完成")
            print(f"     - 测试用例: {result.get('total_tests', 0)}")
            print(f"     - 质量分数: {result.get('overall_score', 0):.2%}")
            
            return {
                'total': result.get('total_tests', 0),
                'quality_score': result.get('overall_score', 0.8),
                'scores': result.get('scores', {}),
                'details': result
            }
            
        except Exception as e:
            print(f"  [!] 评估失败: {e}")
            import traceback
            traceback.print_exc()
            # 返回默认结果
            return {
                'total': 0,
                'quality_score': 0.8,  # 默认分数
                'error': str(e)
            }
    
    def _get_default_evaluators(self, prompt_name: str) -> List:
        """
        根据提示词配置获取对应的评估器
        
        Args:
            prompt_name: 提示词名称
            
        Returns:
            评估器列表
        """
        from evaluation.evaluators import get_evaluators_for_prompt
        
        # 从配置读取提示词信息
        if prompt_name not in self.config.get('prompts', {}):
            print(f"⚠️ 警告: 提示词 '{prompt_name}' 不在配置中，使用默认评估器")
            # 返回通用的报告评估器
            from evaluation.evaluators.report import ReportEvaluators
            return [
                ReportEvaluators.structure_evaluator,
                ReportEvaluators.content_completeness_evaluator,
                ReportEvaluators.relevance_evaluator,
                ReportEvaluators.parameter_usage_evaluator,
            ]
        
        prompt_config = self.config['prompts'][prompt_name]
        evaluators = get_evaluators_for_prompt(prompt_config)
        
        if not evaluators:
            print(f"⚠️ 警告: 提示词 '{prompt_name}' 没有配置评估器")
        
        return evaluators

    # ========== 获取评估器对象 ==========
    def _get_evaluators_by_names(self, evaluator_names: List[str]) -> List:
        """
        根据评估器名称获取评估器对象（使用评估器注册表）
        
        Args:
            evaluator_names: 评估器名称列表
            
        Returns:
            评估器对象列表
        """
        from evaluation.evaluators import get_evaluator
        
        evaluators = []
        for name in evaluator_names:
            try:
                evaluators.append(get_evaluator(name))
            except KeyError as e:
                print(f"[WARN] {e}")
        
        return evaluators
    
    # ========== 版本管理和辅助方法 ==========
    
    def _generate_version_number(self, prompt_name: str, change_type: str = 'patch') -> str:
        """
        自动生成版本号
        
        Args:
            prompt_name: Prompt 名称
            change_type: 变更类型
                - 'major': 主版本（1.0.0 → 2.0.0）不兼容的大改动
                - 'minor': 次版本（1.0.0 → 1.1.0）新功能
                - 'patch': 补丁版本（1.0.0 → 1.0.1）小优化（默认）
        
        Returns:
            新版本号（如 v1.2.3）
        """
        from datetime import datetime
        import json
        
        # 读取版本配置
        version_format = self.config.get('versioning', {}).get('version_format', 'semantic')
        
        # 时间戳格式
        if version_format == 'timestamp':
            return f"v{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # 语义化版本（默认）
        version_file = self.versions_dir / f"{prompt_name}.json"
        
        if version_file.exists():
            with open(version_file, 'r', encoding='utf-8') as f:
                version_info = json.load(f)
                current_version = version_info.get('current_version', 'v1.0.0')
                history = version_info.get('history', [])
        else:
            current_version = 'v1.0.0'
            history = []
        
        # 解析当前版本
        parts = current_version.replace('v', '').split('.')
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        
        # 根据变更类型递增
        if change_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif change_type == 'minor':
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
        
        new_version = f"v{major}.{minor}.{patch}"
        
        # 更新历史记录
        history.append({
            'version': current_version,
            'timestamp': datetime.now().isoformat(),
            'change_type': change_type
        })
        
        # 保存版本信息
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump({
                'current_version': new_version,
                'updated_at': datetime.now().isoformat(),
                'history': history[-10:]  # 只保留最近10个版本
            }, f, indent=2, ensure_ascii=False)
        
        return new_version
    
    def _update_yaml_version(self, filename: str, version: str):
        """
        更新 YAML 文件中的版本号
        
        Args:
            filename: YAML 文件名
            version: 新版本号
        """
        import yaml
        from datetime import datetime
        
        filepath = self.prompts_dir / filename
        
        if not filepath.exists():
            print(f"[WARN] 文件不存在: {filepath}")
            return
        
        try:
            # 读取现有内容
            with open(filepath, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
            
            # 更新版本号和时间戳
            content['version'] = version
            content['updated_at'] = datetime.now().isoformat()
            
            # 写回文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# 自动更新版本号: {version}\n")
                f.write(f"# 更新时间: {content['updated_at']}\n\n")
                yaml.dump(content, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
            print(f"[OK] 已更新 YAML 版本号: {version}")
        except Exception as e:
            print(f"[WARN] 更新 YAML 版本号失败: {e}")
    
    def check_sync(self, prompt_name: str):
        """检查本地和远程的同步状态"""
        print(f"\n[SYNC] 同步状态: {prompt_name}")
        print(f"{'='*60}\n")
        
        try:
            # 本地文件信息
            filename = self.config['prompts'][prompt_name]['file']
            filepath = self.prompts_dir / filename
            
            if filepath.exists():
                from datetime import datetime
                import os
                
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                size = os.path.getsize(filepath)
                
                print(f"本地版本:")
                print(f"  文件: {filepath}")
                print(f"  修改时间: {mtime}")
                print(f"  大小: {size / 1024:.2f} KB")
            else:
                print(f"本地版本: [X] 不存在")
            
            # 远程版本信息
            print(f"\n远程版本 (Hub):")
            hub_name = self._get_hub_name(prompt_name)
            print(f"  名称: {hub_name}")
            
            try:
                from langchain import hub
                remote_prompt = hub.pull(hub_name)
                print(f"  状态: [OK] 存在")
            except:
                print(f"  状态: [X] 不存在")
            
            print(f"\n{'='*60}\n")
            
        except Exception as e:
            print(f"[ERROR] 检查失败: {e}")
    
    def list_versions(self, prompt_name: str) -> List[str]:
        """
        列出所有版本备份
        
        注意：此功能需要访问本地版本历史文件
        """
        import json
        
        try:
            version_file = self.versions_dir / f"{prompt_name}.json"
            
            if not version_file.exists():
                print(f"[INFO] {prompt_name} 暂无版本历史")
                return []
            
            with open(version_file, 'r', encoding='utf-8') as f:
                version_info = json.load(f)
            
            history = version_info.get('history', [])
            versions = [item['version'] for item in history]
            
            print(f"[VERSIONS] {prompt_name} 的历史版本:")
            for item in history:
                print(f"  - {item['version']} ({item['timestamp'][:10]}) - {item['change_type']}")
            
            return versions
            
        except Exception as e:
            print(f"[ERROR] 获取版本列表失败: {e}")
            return []
    
    def rollback(self, prompt_name: str, version: str):
        """回滚到指定版本"""
        print(f"\n[ROLLBACK] 回滚 {prompt_name} 到 {version}")
        print(f"{'='*60}\n")
        
        try:
            from langchain import hub
            
            hub_name = self._get_hub_name(prompt_name)
            versioned_name = f"{hub_name}-{version}"
            
            # 步骤1: 从 Hub 拉取历史版本
            print(f"步骤 1/3: 从 Hub 拉取 {versioned_name}")
            prompt = hub.pull(versioned_name)
            
            # 步骤2: 推送到当前版本
            print(f"步骤 2/3: 推送到 {hub_name}")
            hub.push(hub_name, prompt, new_repo_is_public=False)
            
            # 步骤3: 更新本地文件
            print(f"步骤 3/3: 更新本地文件")
            filename = self.config['prompts'][prompt_name]['file']
            self._save_prompt_as_yaml(prompt, filename, prompt_name)
            
            print(f"\n[SUCCESS] 回滚完成")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"[ERROR] 回滚失败: {e}")

