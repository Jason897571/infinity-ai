"""
进度追踪器 - 记录Agent的所有动作和进度
"""
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..utils.file_manager import FileManager
from ..utils.logger import get_logger, ProgressLogger


class ProgressTracker:
    """进度追踪器

    负责记录Agent的所有动作到claude-progress.txt文件
    """

    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self.file_manager = FileManager(Path.cwd())
        self.logger = get_logger("progress_tracker")
        self.progress_logger = ProgressLogger(progress_file)

    def log_session_start(self, session_id: str, agent_type: str):
        """记录会话开始

        Args:
            session_id: 会话ID
            agent_type: Agent类型（initializer/coding_agent）
        """
        separator = "=" * 80
        message = f"""
{separator}
SESSION START: {session_id}
Agent Type: {agent_type}
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{separator}
"""
        self.file_manager.append_to_file(self.progress_file, message)
        self.logger.info(f"Session started: {session_id}")

    def log_session_end(self, session_id: str, summary: str, features_completed: int = 0):
        """记录会话结束

        Args:
            session_id: 会话ID
            summary: 会话摘要
            features_completed: 完成的功能数量
        """
        separator = "=" * 80
        message = f"""
SESSION END: {session_id}
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Features Completed: {features_completed}
Summary: {summary}
{separator}
"""
        self.file_manager.append_to_file(self.progress_file, message)
        self.logger.info(f"Session ended: {session_id}")

    def log_action(self, action: str, details: str = ""):
        """记录Agent动作

        Args:
            action: 动作描述
            details: 详细信息
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{timestamp}] {action}\n"

        if details:
            message += f"  Details: {details}\n"

        self.file_manager.append_to_file(self.progress_file, message)
        self.logger.info(f"Action logged: {action}")

    def log_feature_start(self, feature_id: str, description: str):
        """记录开始处理功能"""
        self.log_action(
            f"STARTED FEATURE: {feature_id}",
            f"Description: {description}"
        )

    def log_feature_complete(self, feature_id: str, passed: bool, notes: str = ""):
        """记录功能完成"""
        status = "PASSED" if passed else "FAILED"
        self.log_action(
            f"COMPLETED FEATURE: {feature_id} - {status}",
            notes
        )

    def log_code_change(self, file_path: str, change_type: str, description: str):
        """记录代码变更

        Args:
            file_path: 文件路径
            change_type: 变更类型（created/modified/deleted）
            description: 变更描述
        """
        self.log_action(
            f"CODE {change_type.upper()}: {file_path}",
            description
        )

    def log_test_result(self, test_name: str, passed: bool, output: str = ""):
        """记录测试结果

        Args:
            test_name: 测试名称
            passed: 是否通过
            output: 测试输出
        """
        status = "PASSED" if passed else "FAILED"
        self.log_action(
            f"TEST {status}: {test_name}",
            output[:500]  # 限制输出长度
        )

    def log_git_commit(self, commit_hash: str, message: str):
        """记录Git提交"""
        self.log_action(
            f"GIT COMMIT: {commit_hash[:8]}",
            message
        )

    def log_error(self, error: str, context: str = ""):
        """记录错误"""
        self.log_action(
            f"ERROR: {error}",
            context
        )

    def log_thinking(self, thought: str):
        """记录Agent的思考过程"""
        self.log_action(
            "THINKING",
            thought
        )

    def get_recent_progress(self, lines: int = 100) -> str:
        """获取最近的进度记录

        Args:
            lines: 读取的行数

        Returns:
            最近N行的进度记录
        """
        if not self.progress_file.exists():
            return ""

        content = self.file_manager.read_file(self.progress_file)
        if not content:
            return ""

        all_lines = content.split('\n')
        recent_lines = all_lines[-lines:]

        return '\n'.join(recent_lines)

    def get_session_count(self) -> int:
        """获取会话次数"""
        if not self.progress_file.exists():
            return 0

        content = self.file_manager.read_file(self.progress_file)
        if not content:
            return 0

        return content.count("SESSION START")

    def get_feature_completion_count(self) -> int:
        """获取功能完成次数"""
        if not self.progress_file.exists():
            return 0

        content = self.file_manager.read_file(self.progress_file)
        if not content:
            return 0

        return content.count("COMPLETED FEATURE")

    def generate_summary(self) -> Dict[str, Any]:
        """生成进度摘要

        Returns:
            {
                'total_sessions': int,
                'total_features_completed': int,
                'last_session': str,
                'recent_actions': List[str]
            }
        """
        recent = self.get_recent_progress(50)
        lines = [line for line in recent.split('\n') if line.strip()]

        return {
            'total_sessions': self.get_session_count(),
            'total_features_completed': self.get_feature_completion_count(),
            'last_session': recent,
            'recent_actions': lines[-10:] if lines else []
        }