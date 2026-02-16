"""
编码Agent - 后续会话运行，实现功能
"""
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import time

from anthropic import Anthropic
from ..config.settings import Settings
from ..config.llm_config import LLMConfig
from ..utils.git_utils import GitManager
from ..utils.file_manager import FileManager
from ..utils.browser_tester import BrowserTester
from ..utils.logger import get_logger
from .progress_tracker import ProgressTracker
from .feature_manager import FeatureManager


class CodingAgent:
    """编码Agent

    在后续会话运行，负责：
    1. 读取进度和功能列表
    2. 选择一个未完成的功能
    3. 实现该功能
    4. 测试验证
    5. 提交代码
    """

    def __init__(
        self,
        project_root: Path,
        settings: Settings,
        llm_config: LLMConfig
    ):
        self.project_root = Path(project_root)
        self.settings = settings
        self.llm_config = llm_config

        # 初始化工具
        self.git_manager = GitManager(self.project_root)
        self.file_manager = FileManager(self.project_root)
        self.progress_tracker = ProgressTracker(self.project_root / self.settings.progress_file)
        self.feature_manager = FeatureManager(self.project_root / self.settings.feature_list_file)
        self.browser_tester = BrowserTester(
            headless=self.settings.browser_headless,
            timeout=self.settings.test_timeout
        )

        # 初始化Claude客户端
        client_kwargs = {"api_key": llm_config.api_key}
        if llm_config.api_base_url:
            client_kwargs["base_url"] = llm_config.api_base_url
        self.client = Anthropic(**client_kwargs)
        self.logger = get_logger("coding_agent")

        # 会话信息
        self.session_id = f"coding_{uuid.uuid4().hex[:8]}"

    def run_session(self) -> bool:
        """执行一个完整的会话

        Returns:
            是否成功完成至少一个功能
        """
        self.logger.info(f"Starting coding session: {self.session_id}")
        self.progress_tracker.log_session_start(self.session_id, "coding_agent")

        try:
            # 1. 读取当前状态
            self.progress_tracker.log_action("Reading current state")
            state = self._read_current_state()

            # 2. 启动开发服务器（如果需要）
            self.progress_tracker.log_action("Checking development server")
            self._ensure_dev_server_running()

            # 3. 运行基本测试
            self.progress_tracker.log_action("Running basic E2E test")
            if not self._run_basic_test():
                self.logger.warning("Basic test failed, there might be existing issues")

            # 4. 选择下一个功能
            feature = self.feature_manager.get_next_incomplete_feature()
            if not feature:
                self.progress_tracker.log_action("All features completed!")
                self.progress_tracker.log_session_end(
                    self.session_id,
                    "All features already completed",
                    0
                )
                return True

            self.progress_tracker.log_feature_start(feature.id, feature.description)

            # 5. 实现功能
            self.progress_tracker.log_action(f"Implementing feature: {feature.id}")
            success = self._implement_feature(feature, state)

            if success:
                # 6. 测试功能
                self.progress_tracker.log_action(f"Testing feature: {feature.id}")
                test_passed = self._test_feature(feature)

                # 7. 标记功能状态
                if test_passed:
                    self.feature_manager.mark_feature_complete(feature.id)
                    self.progress_tracker.log_feature_complete(feature.id, True)

                    # 8. 提交代码
                    self.progress_tracker.log_action("Creating git commit")
                    self.git_manager.create_commit_for_feature(
                        feature.description,
                        f"Feature: {feature.id}\nTest: {'PASSED' if test_passed else 'FAILED'}"
                    )

                    self.progress_tracker.log_session_end(
                        self.session_id,
                        f"Successfully completed feature: {feature.description}",
                        1
                    )
                    return True
                else:
                    self.feature_manager.mark_feature_failed(feature.id, "Tests failed")
                    self.progress_tracker.log_feature_complete(feature.id, False, "Tests failed")
                    return False
            else:
                self.progress_tracker.log_error("Failed to implement feature")
                return False

        except Exception as e:
            self.logger.error(f"Session failed: {e}")
            self.progress_tracker.log_error(str(e), "Session failed")
            self.progress_tracker.log_session_end(
                self.session_id,
                f"Session failed: {str(e)}",
                0
            )
            return False

    def _read_current_state(self) -> Dict[str, Any]:
        """读取当前项目状态

        Returns:
            {
                'git_logs': list,
                'progress': str,
                'features': list,
                'recent_changes': str
            }
        """
        # 读取Git日志
        commits = self.git_manager.get_recent_commits(10)

        # 读取进度
        progress = self.progress_tracker.get_recent_progress(100)

        # 获取功能摘要
        feature_summary = self.feature_manager.get_progress_summary()

        # 获取Git差异
        diff = self.git_manager.get_diff()

        return {
            'git_logs': commits,
            'progress': progress,
            'features': feature_summary,
            'recent_changes': diff
        }

    def _ensure_dev_server_running(self):
        """确保开发服务器正在运行"""
        # 这里可以添加检查逻辑
        # 目前只是记录日志
        self.progress_tracker.log_action(
            "Development server check",
            "Assuming server is running. Use init.sh to start if needed."
        )

    def _run_basic_test(self) -> bool:
        """运行基本的端到端测试

        Returns:
            是否通过
        """
        test_script = self.browser_tester.create_basic_e2e_test()

        try:
            result = self.browser_tester.test_feature([
                "Navigate to http://localhost:3000",
                "Verify body exists"
            ])

            passed = result['success']
            self.progress_tracker.log_test_result("Basic E2E", passed, result.get('output', ''))
            return passed
        except Exception as e:
            self.logger.warning(f"Basic test failed: {e}")
            return False

    def _implement_feature(self, feature: Any, state: Dict[str, Any]) -> bool:
        """使用Claude实现功能

        Args:
            feature: 要实现的功能
            state: 当前项目状态

        Returns:
            是否成功
        """
        prompt = f"""
You are a software developer working on a web application. Your task is to implement the following feature.

Current Project State:
- Git commits: {len(state['git_logs'])} recent commits
- Features completed: {state['features']['completed']}/{state['features']['total']}
- Recent progress: {state['progress'][-500:]}

Feature to Implement:
ID: {feature.id}
Description: {feature.description}
Category: {feature.category}
Priority: {feature.priority}

Test Steps (you must ensure all these pass):
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(feature.steps))}

Instructions:
1. Analyze the feature requirements
2. Identify what files need to be created or modified
3. Provide the complete code for each file
4. Ensure the code follows best practices
5. Include error handling where appropriate

For each file, provide:
- File path
- Complete file content
- Brief explanation of changes

Format your response as:
```
FILE: path/to/file
EXPLANATION: ...
CONTENT:
[full file content]

FILE: path/to/another/file
EXPLANATION: ...
CONTENT:
[full file content]
```

Implement the feature now:
"""

        try:
            message = self.client.messages.create(
                model=self.llm_config.model,
                max_tokens=self.llm_config.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            content = message.content[0].text

            # 解析响应并写入文件
            files_created = self._parse_and_write_files(content)

            if files_created:
                self.progress_tracker.log_action(
                    f"Created/Modified {len(files_created)} files",
                    ", ".join(files_created)
                )
                return True
            else:
                self.logger.error("No files were created from Claude response")
                return False

        except Exception as e:
            self.logger.error(f"Failed to implement feature: {e}")
            self.progress_tracker.log_error(str(e), "Feature implementation failed")
            return False

    def _parse_and_write_files(self, response: str) -> List[str]:
        """解析Claude响应并写入文件

        Args:
            response: Claude的响应文本

        Returns:
            创建/修改的文件列表
        """
        import re

        files_written = []

        # 分割响应为多个文件块
        file_blocks = re.split(r'FILE:\s+', response)

        for block in file_blocks:
            if not block.strip():
                continue

            # 提取文件路径
            lines = block.split('\n')
            if not lines:
                continue

            file_path = lines[0].strip()

            # 查找CONTENT部分
            content_match = re.search(r'CONTENT:\s*\n(.*?)(?=FILE:|$)', block, re.DOTALL)

            if content_match:
                content = content_match.group(1).strip()

                # 如果内容被代码块包裹，提取它
                if content.startswith('```'):
                    # 移除代码块标记
                    lines = content.split('\n')
                    if lines[0].startswith('```'):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == '```':
                        lines = lines[:-1]
                    content = '\n'.join(lines)

                # 写入文件
                success = self.file_manager.write_file(file_path, content)
                if success:
                    files_written.append(file_path)
                    self.progress_tracker.log_code_change(file_path, "modified", f"Implemented feature")

        return files_written

    def _test_feature(self, feature: Any) -> bool:
        """测试功能

        Args:
            feature: 要测试的功能

        Returns:
            是否通过测试
        """
        try:
            result = self.browser_tester.test_feature(feature.steps)

            passed = result['success']
            self.progress_tracker.log_test_result(
                f"Feature: {feature.id}",
                passed,
                result.get('output', '')
            )

            return passed

        except Exception as e:
            self.logger.error(f"Test failed: {e}")
            self.progress_tracker.log_test_result(
                f"Feature: {feature.id}",
                False,
                str(e)
            )
            return False

    def run_continuous(self, max_iterations: int = 100):
        """连续运行多个会话

        Args:
            max_iterations: 最大迭代次数
        """
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            self.logger.info(f"Starting iteration {iteration}/{max_iterations}")

            # 运行一个会话
            success = self.run_session()

            # 检查是否所有功能都完成了
            summary = self.feature_manager.get_progress_summary()
            if summary['pending'] == 0:
                self.logger.info("All features completed!")
                break

            # 为下一次迭代生成新的session ID
            self.session_id = f"coding_{uuid.uuid4().hex[:8]}"

            # 短暂休息
            time.sleep(2)

        self.logger.info(f"Completed {iteration} iterations")