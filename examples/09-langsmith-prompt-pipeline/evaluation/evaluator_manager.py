"""
Evaluator 管理器模块
负责 Evaluator 的上传、同步、版本管理等功能
支持标准的 LangSmith Evaluator API 和自动同步
"""
import sys
import os
import yaml
import inspect
import ast
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import importlib.util

# 确保 Windows 控制台正确显示 UTF-8
if sys.platform == 'win32' and not hasattr(sys.stdout, 'reconfigure'):
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='ignore')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='ignore')
    except (AttributeError, OSError):
        pass

from config.langsmith_config import LangSmithConfig


class EvaluatorManager:
    """Evaluator 管理器类
    
    核心理念：与 PromptManager 对称设计
    - 支持从本地 Python 文件提取 evaluator
    - 推送到 LangSmith 平台
    - 从平台拉取最新版本
    - 版本管理和同步
    """
    
    def __init__(self, evaluators_dir: str = "evaluation/evaluators", config_file: str = "evaluators_config.yaml", auto_pull: bool = False):
        """
        初始化 Evaluator 管理器
        
        Args:
            evaluators_dir: Evaluator 文件存储目录
            config_file: Evaluator 配置文件名
            auto_pull: 是否自动从平台拉取最新版本（默认 False，因为代码通常本地管理）
        """
        self.evaluators_dir = Path(evaluators_dir)
        if not self.evaluators_dir.exists():
            raise FileNotFoundError(f"Evaluator 目录不存在: {evaluators_dir}")
        
        # 加载配置
        self.config_path = self.evaluators_dir.parent / config_file
        self.config = self._load_config()
        self.auto_pull = auto_pull
        
        # 版本信息存储目录
        self.versions_dir = self.evaluators_dir.parent / ".evaluator_versions"
        self.versions_dir.mkdir(exist_ok=True)
        
        # LangSmith Client（延迟初始化）
        self._client = None
    
    def _load_config(self) -> Dict[str, Any]:
        """加载 evaluator 配置文件"""
        if not self.config_path.exists():
            # 创建默认配置
            default_config = {
                'evaluators': {},
                'versioning': {
                    'version_format': 'semantic',
                    'create_backup': False
                }
            }
            self._save_config(default_config)
            return default_config
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {'evaluators': {}, 'versioning': {}}
    
    def _save_config(self, config: Dict[str, Any] = None):
        """保存配置文件"""
        config = config or self.config
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    @property
    def client(self):
        """获取 LangSmith Client（单例模式）"""
        if self._client is None:
            self._client = LangSmithConfig.get_client()
        return self._client
    
    def _get_evaluator_source_code(self, evaluator_name: str, class_name: Optional[str] = None) -> str:
        """
        从 Python 文件中提取 evaluator 函数的源代码
        
        Args:
            evaluator_name: Evaluator 函数名称（如 'structure_evaluator'）
            class_name: 所属类名（如 'ReportEvaluators'），如果为 None 则自动检测
            
        Returns:
            Evaluator 函数的完整源代码（包含导入和依赖）
        """
        # 从配置中获取文件信息
        evaluator_config = self.config.get('evaluators', {}).get(evaluator_name, {})
        file_path = evaluator_config.get('file', None)
        class_name = class_name or evaluator_config.get('class', None)
        
        if not file_path:
            # 尝试自动查找
            for py_file in self.evaluators_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                try:
                    source = self._extract_from_file(py_file, evaluator_name, class_name)
                    if source:
                        return source
                except:
                    continue
            raise ValueError(f"未找到 evaluator: {evaluator_name}")
        
        file_path = self.evaluators_dir / file_path if not Path(file_path).is_absolute() else Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Evaluator 文件不存在: {file_path}")
        
        return self._extract_from_file(file_path, evaluator_name, class_name)
    
    def _extract_from_file(self, file_path: Path, evaluator_name: str, class_name: Optional[str] = None) -> str:
        """
        从文件中提取 evaluator 源代码
        
        Args:
            file_path: Python 文件路径
            evaluator_name: 函数名称
            class_name: 类名（可选）
            
        Returns:
            完整的源代码字符串
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # 解析 AST
        tree = ast.parse(source_code)
        
        # 查找函数或方法
        evaluator_func = None
        imports = []
        found_class = None
        
        # 先收集所有导入
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else ""))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = ", ".join([alias.name + (f" as {alias.asname}" if alias.asname else "") for alias in node.names])
                imports.append(f"from {module} import {names}")
        
        # 查找类和函数
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if class_name and node.name == class_name:
                    found_class = node
                    # 在类中查找方法
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == evaluator_name:
                            evaluator_func = item
                            found_class = node
                            break
                elif not class_name:
                    # 未指定类名，查找所有类中的方法
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == evaluator_name:
                            evaluator_func = item
                            found_class = node
                            break
            elif isinstance(node, ast.FunctionDef) and node.name == evaluator_name and not class_name and not found_class:
                # 顶级函数
                evaluator_func = node
        
        if not evaluator_func:
            return None
        
        # 提取函数源代码（使用行号范围）
        start_line = evaluator_func.lineno - 1  # AST 行号从 1 开始，列表从 0 开始
        end_line = evaluator_func.end_lineno if hasattr(evaluator_func, 'end_lineno') else evaluator_func.lineno
        
        lines = source_code.split('\n')
        func_lines = lines[start_line:end_line]
        
        # 如果是类方法，需要去除类方法的缩进
        if found_class:
            # 检测第一行的缩进级别（类方法的缩进）
            first_line = func_lines[0] if func_lines else ""
            class_indent = len(first_line) - len(first_line.lstrip())
            
            # 去除类方法级别的缩进，但保留函数内部的相对缩进
            dedented_lines = []
            for i, line in enumerate(func_lines):
                if line.strip():  # 非空行
                    current_indent = len(line) - len(line.lstrip())
                    # 去除类级别的缩进
                    new_indent = max(0, current_indent - class_indent)
                    dedented_lines.append(" " * new_indent + line.lstrip())
                else:
                    dedented_lines.append("")
            
            func_source = '\n'.join(dedented_lines)
        else:
            func_source = '\n'.join(func_lines)
        
        # 如果是类方法，需要包含类装饰器逻辑
        if found_class:
            # 查找方法的装饰器
            decorators = []
            for decorator in evaluator_func.decorator_list:
                decorator_source = ast.get_source_segment(source_code, decorator)
                if decorator_source:
                    decorators.append(f"@{decorator_source}")
            
            if decorators:
                func_source = "\n".join(decorators) + "\n" + func_source
        
        # 组合完整代码（去重导入）
        unique_imports = list(dict.fromkeys(imports))  # 保持顺序的去重
        full_code = "\n".join(unique_imports) + "\n\n" + func_source
        
        return full_code
    
    def list_evaluators(self) -> Dict[str, str]:
        """列出所有可用的 Evaluator"""
        evaluators_info = {}
        for name, info in self.config.get('evaluators', {}).items():
            evaluators_info[name] = info.get('description', 'No description')
        return evaluators_info
    
    def register_evaluator(
        self,
        evaluator_name: str,
        file_path: str,
        description: str = "",
        class_name: Optional[str] = None,
        dataset_name: Optional[str] = None
    ):
        """
        注册一个 evaluator 到配置中
        
        Args:
            evaluator_name: Evaluator 名称
            file_path: Python 文件路径（相对或绝对）
            description: 描述
            class_name: 所属类名（如果 evaluator 是类方法）
            dataset_name: 关联的数据集名称
        """
        if 'evaluators' not in self.config:
            self.config['evaluators'] = {}
        
        self.config['evaluators'][evaluator_name] = {
            'file': file_path,
            'description': description,
            'class': class_name,
            'dataset': dataset_name,
            'created_at': datetime.now().isoformat()
        }
        
        self._save_config()
        print(f"✓ 已注册 evaluator: {evaluator_name}")
    
    def push(self, evaluator_name: str, dataset_name: Optional[str] = None, description: Optional[str] = None) -> bool:
        """
        推送本地 evaluator 到 LangSmith 平台
        
        Args:
            evaluator_name: Evaluator 名称
            dataset_name: 数据集名称（用于在平台上关联）
            description: 描述（可选，覆盖配置中的描述）
            
        Returns:
            bool: 推送是否成功
        """
        print(f"\n{'='*60}")
        print(f"[PUSH] 推送 {evaluator_name} 到 LangSmith")
        print(f"{'='*60}\n")
        
        try:
            # 步骤1: 验证配置
            print("[1/3] 步骤 1/3: 验证 Evaluator 配置...")
            if evaluator_name not in self.config.get('evaluators', {}):
                # 尝试自动注册
                print(f"  [!] {evaluator_name} 未在配置中，尝试自动发现...")
                # 这里可以添加自动发现逻辑
                raise ValueError(f"Evaluator '{evaluator_name}' 未在配置中注册。请先使用 register_evaluator() 注册。")
            
            print("[OK] 配置验证通过")
            
            # 步骤2: 提取源代码
            print("\n[2/3] 步骤 2/3: 提取 Evaluator 源代码...")
            evaluator_config = self.config['evaluators'][evaluator_name]
            source_code = self._get_evaluator_source_code(
                evaluator_name,
                evaluator_config.get('class')
            )
            
            if not source_code:
                raise ValueError(f"无法提取 {evaluator_name} 的源代码")
            
            print(f"[OK] 源代码提取成功 ({len(source_code)} 字符)")
            
            # 步骤3: 创建/更新 LangSmith Evaluator
            print("\n[3/3] 步骤 3/3: 创建/更新 LangSmith Evaluator...")
            
            eval_description = description or evaluator_config.get('description', f"Evaluator: {evaluator_name}")
            dataset = dataset_name or evaluator_config.get('dataset')
            
            # 创建 evaluator 配置
            evaluator_data = {
                "name": evaluator_name,
                "description": eval_description,
                "code": source_code,
                "language": "python",
                "is_public": False
            }
            
            # 尝试创建或更新
            try:
                # 检查是否已存在
                existing = self._find_evaluator_on_platform(evaluator_name)
                
                if existing:
                    print(f"  [INFO] Evaluator '{evaluator_name}' 已存在，更新中...")
                    # 更新现有 evaluator（如果 API 支持）
                    # 注意：LangSmith API 可能需要不同的方法
                    evaluator_id = self._create_or_update_evaluator(evaluator_data, existing.get('id'))
                else:
                    print(f"  [INFO] 创建新的 Evaluator '{evaluator_name}'...")
                    evaluator_id = self._create_or_update_evaluator(evaluator_data)
                
                print(f"[OK] Evaluator 已同步到 LangSmith")
                print(f"  名称: {evaluator_name}")
                print(f"  查看: https://smith.langchain.com/datasets/{dataset}/evaluators" if dataset else "https://smith.langchain.com/evaluators")
                
                # 更新配置中的同步信息
                self.config['evaluators'][evaluator_name]['synced_at'] = datetime.now().isoformat()
                self.config['evaluators'][evaluator_name]['langsmith_id'] = evaluator_id
                self._save_config()
                
            except Exception as e:
                print(f"[WARN] LangSmith API 调用失败: {e}")
                print(f"  这可能是因为 API 方法不同或需要手动创建")
                print(f"  请参考 LangSmith 文档: https://docs.langsmith.com/api/evaluators")
                print(f"  源代码已准备好，可以手动上传:")
                print(f"  - 访问: https://smith.langchain.com/datasets/{dataset}/evaluators" if dataset else "https://smith.langchain.com/evaluators")
                print(f"  - 选择 'Create Custom Code Evaluator'")
                print(f"  - 粘贴以下代码:\n")
                print("-" * 60)
                print(source_code)
                print("-" * 60)
                
                # 保存源代码到临时文件
                temp_file = self.evaluators_dir.parent / f"{evaluator_name}_source.py"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(source_code)
                print(f"\n  源代码已保存到: {temp_file}")
                
                return False
            
            print(f"\n{'='*60}")
            print("[SUCCESS] 推送完成！")
            print(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] 推送失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _find_evaluator_on_platform(self, evaluator_name: str) -> Optional[Dict[str, Any]]:
        """
        在 LangSmith 平台上查找 evaluator
        
        Args:
            evaluator_name: Evaluator 名称
            
        Returns:
            Evaluator 信息（如果存在）或 None
        """
        try:
            # 注意：LangSmith Client API 可能没有直接的 list_evaluators 方法
            # 这里需要根据实际 API 调整
            # 可能的方法：
            # - client.list_evaluators()
            # - client.get_evaluator(name=evaluator_name)
            
            # 暂时返回 None，表示未找到
            # 实际实现需要查阅 LangSmith API 文档
            return None
            
        except Exception as e:
            print(f"[WARN] 查找 evaluator 失败: {e}")
            return None
    
    def _create_or_update_evaluator(self, evaluator_data: Dict[str, Any], evaluator_id: Optional[str] = None) -> str:
        """
        创建或更新 LangSmith Evaluator
        
        Args:
            evaluator_data: Evaluator 数据
            evaluator_id: 现有 Evaluator ID（如果更新）
            
        Returns:
            Evaluator ID
        """
        # 注意：这里需要根据实际的 LangSmith API 实现
        # 可能的方法：
        # - client.create_evaluator(**evaluator_data)
        # - client.update_evaluator(evaluator_id, **evaluator_data)
        
        # 由于 LangSmith API 的具体方法可能需要进一步确认，
        # 这里先提供一个占位实现
        try:
            # 尝试使用可能的 API 方法
            if hasattr(self.client, 'create_evaluator'):
                if evaluator_id:
                    result = self.client.update_evaluator(evaluator_id, **evaluator_data)
                else:
                    result = self.client.create_evaluator(**evaluator_data)
                return str(result.id) if hasattr(result, 'id') else str(result)
            else:
                # API 方法不存在，抛出异常
                raise AttributeError("LangSmith Client 不支持 create_evaluator 方法")
                
        except AttributeError:
            # 如果 API 不存在，返回一个占位 ID
            # 实际使用中需要根据 LangSmith 最新 API 文档调整
            return evaluator_data.get('name', 'unknown')
    
    def pull(self, evaluator_name: str, save_to_file: bool = True) -> bool:
        """
        从 LangSmith 平台拉取 evaluator 代码
        
        注意：需要 LangSmith API 支持获取 evaluator 代码
        如果 API 不支持，会尝试通过其他方式获取
        
        Args:
            evaluator_name: Evaluator 名称
            save_to_file: 是否保存到本地文件（默认 True）
            
        Returns:
            bool: 拉取是否成功
        """
        print(f"\n[PULL] 从 LangSmith 拉取 {evaluator_name}...")
        print("=" * 60)
        
        try:
            # 尝试查找平台上的 evaluator
            platform_evaluator = self._find_evaluator_on_platform(evaluator_name)
            
            if not platform_evaluator:
                print(f"[WARN] 平台上的 evaluator '{evaluator_name}' 不存在")
                print(f"\n💡 提示：")
                print(f"  1. 确认 evaluator 名称正确")
                print(f"  2. 确认 evaluator 已上传到平台")
                print(f"  3. 访问平台查看：https://smith.langchain.com/datasets/<dataset_name>/evaluators")
                return False
            
            # 尝试获取代码
            evaluator_code = None
            try:
                # 尝试通过 API 获取代码
                if hasattr(platform_evaluator, 'code'):
                    evaluator_code = platform_evaluator.code
                elif isinstance(platform_evaluator, dict) and 'code' in platform_evaluator:
                    evaluator_code = platform_evaluator['code']
                elif hasattr(self.client, 'get_evaluator'):
                    # 尝试通过 client 获取
                    full_evaluator = self.client.get_evaluator(evaluator_name=evaluator_name)
                    if hasattr(full_evaluator, 'code'):
                        evaluator_code = full_evaluator.code
            except Exception as e:
                print(f"[WARN] 无法通过 API 获取代码: {e}")
            
            if not evaluator_code:
                print(f"[WARN] 无法获取 evaluator 代码")
                print(f"\n💡 解决方案：")
                print(f"  1. 手动从平台复制代码")
                print(f"    访问：https://smith.langchain.com/datasets/<dataset_name>/evaluators")
                print(f"    找到 '{evaluator_name}'，查看代码")
                print(f"  2. 或者在本地重新实现 evaluator")
                print(f"    文件：evaluation/evaluators/<file>.py")
                
                # 仍然更新元数据
                if evaluator_name in self.config.get('evaluators', {}):
                    self.config['evaluators'][evaluator_name].update({
                        'synced_at': datetime.now().isoformat(),
                        'platform_description': platform_evaluator.get('description', '')
                    })
                    self._save_config()
                
                return False
            
            # 获取代码成功
            print(f"[OK] 成功获取代码 ({len(evaluator_code)} 字符)")
            
            # 保存到本地文件
            if save_to_file:
                # 确定保存路径
                evaluator_config = self.config.get('evaluators', {}).get(evaluator_name, {})
                source_file = evaluator_config.get('file', f"{evaluator_name}.py")
                target_file = self.evaluators_dir / f"{evaluator_name}_from_platform.py"
                
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(f"# 从 LangSmith 平台拉取的 evaluator 代码\n")
                    f.write(f"# Evaluator: {evaluator_name}\n")
                    f.write(f"# 拉取时间: {datetime.now().isoformat()}\n")
                    f.write(f"# 平台描述: {platform_evaluator.get('description', '')}\n\n")
                    f.write(evaluator_code)
                
                print(f"[OK] 代码已保存到: {target_file}")
                print(f"\n💡 下一步：")
                print(f"  1. 查看拉取的代码: {target_file}")
                print(f"  2. 根据需要集成到本地代码")
                print(f"  3. 更新 evaluation/evaluators/ 目录中的文件")
            
            # 更新配置
            if evaluator_name in self.config.get('evaluators', {}):
                self.config['evaluators'][evaluator_name].update({
                    'synced_at': datetime.now().isoformat(),
                    'platform_description': platform_evaluator.get('description', ''),
                    'pulled_from_platform': True,
                    'platform_code_length': len(evaluator_code)
                })
                self._save_config()
            
            print(f"\n[SUCCESS] 拉取完成！")
            return True
            
        except Exception as e:
            print(f"[ERROR] 拉取失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def validate(self, evaluator_name: str) -> Dict[str, Any]:
        """
        验证 Evaluator 格式和配置
        
        Args:
            evaluator_name: Evaluator 名称
            
        Returns:
            验证结果字典
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # 检查配置
            if evaluator_name not in self.config.get('evaluators', {}):
                result['is_valid'] = False
                result['errors'].append(f"Evaluator '{evaluator_name}' 未在配置中")
                return result
            
            # 检查源代码是否可提取
            try:
                source = self._get_evaluator_source_code(evaluator_name)
                if not source:
                    result['is_valid'] = False
                    result['errors'].append("无法提取源代码")
                else:
                    # 尝试解析代码
                    try:
                        compile(source, f"<{evaluator_name}>", "exec")
                    except SyntaxError as e:
                        result['is_valid'] = False
                        result['errors'].append(f"代码语法错误: {e}")
            except Exception as e:
                result['is_valid'] = False
                result['errors'].append(f"提取源代码失败: {e}")
            
            return result
            
        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f"验证过程出错: {str(e)}")
            return result


def main():
    """主函数 - 命令行界面"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="LangSmith Evaluator 管理器 - 同步评估器到平台"
    )
    
    parser.add_argument(
        "action",
        choices=["push", "pull", "list", "register", "validate"],
        help="操作类型"
    )
    
    parser.add_argument(
        "--name",
        required=True,
        help="Evaluator 名称"
    )
    
    parser.add_argument(
        "--file",
        help="Python 文件路径（register 时使用）"
    )
    
    parser.add_argument(
        "--description",
        help="描述（register/push 时使用）"
    )
    
    parser.add_argument(
        "--class",
        dest="class_name",
        help="所属类名（如果 evaluator 是类方法）"
    )
    
    parser.add_argument(
        "--dataset",
        help="数据集名称"
    )
    
    args = parser.parse_args()
    
    # 创建管理器
    manager = EvaluatorManager()
    
    try:
        if args.action == "push":
            manager.push(
                args.name,
                dataset_name=args.dataset,
                description=args.description
            )
        elif args.action == "pull":
            manager.pull(args.name)
        elif args.action == "list":
            evaluators = manager.list_evaluators()
            print("\n可用的 Evaluators:")
            print("-" * 60)
            for name, desc in evaluators.items():
                print(f"{name:<30} {desc}")
        elif args.action == "register":
            if not args.file:
                print("[ERROR] --file 参数必需")
                sys.exit(1)
            manager.register_evaluator(
                args.name,
                args.file,
                description=args.description or "",
                class_name=args.class_name,
                dataset_name=args.dataset
            )
        elif args.action == "validate":
            result = manager.validate(args.name)
            if result['is_valid']:
                print(f"[OK] {args.name} 验证通过")
            else:
                print(f"[ERROR] {args.name} 验证失败:")
                for error in result['errors']:
                    print(f"  - {error}")
                for warning in result['warnings']:
                    print(f"  - {warning} (警告)")
                sys.exit(1)
        
    except Exception as e:
        print(f"\n[ERROR] 操作失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

