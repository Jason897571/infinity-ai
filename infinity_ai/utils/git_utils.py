"""
Git管理工具
"""
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime
from .logger import get_logger


class GitManager:
    """Git仓库管理器"""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.logger = get_logger("git")

    def is_repo(self) -> bool:
        """检查是否是Git仓库"""
        git_dir = self.repo_root / ".git"
        return git_dir.exists()

    def init_repo(self) -> bool:
        """初始化Git仓库"""
        if self.is_repo():
            self.logger.info("Git repository already exists")
            return True

        try:
            result = subprocess.run(
                ["git", "init"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            self.logger.info("Git repository initialized")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to initialize git repo: {e.stderr}")
            return False

    def get_current_branch(self) -> Optional[str]:
        """获取当前分支名"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def get_status(self) -> Tuple[List[str], List[str], List[str]]:
        """获取仓库状态

        Returns:
            (modified_files, untracked_files, staged_files)
        """
        try:
            # 获取修改的文件
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            modified = []
            untracked = []
            staged = []

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                status = line[:2]
                filepath = line[3:]

                if status.startswith('??'):
                    untracked.append(filepath)
                elif status.startswith((' M', 'M ')):
                    modified.append(filepath)
                elif status.startswith('A '):
                    staged.append(filepath)

            return modified, untracked, staged

        except subprocess.CalledProcessError:
            return [], [], []

    def add_files(self, files: List[str]) -> bool:
        """添加文件到暂存区"""
        if not files:
            return True

        try:
            subprocess.run(
                ["git", "add"] + files,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            self.logger.info(f"Added files to staging: {files}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to add files: {e.stderr}")
            return False

    def commit(self, message: str) -> bool:
        """创建提交"""
        try:
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            self.logger.info(f"Committed: {message}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to commit: {e.stderr}")
            return False

    def get_recent_commits(self, count: int = 10) -> List[dict]:
        """获取最近的提交记录

        Returns:
            [{'hash': str, 'message': str, 'author': str, 'date': str}, ...]
        """
        try:
            result = subprocess.run(
                [
                    "git", "log",
                    f"-{count}",
                    "--pretty=format:%H|%s|%an|%ad",
                    "--date=iso"
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('|')
                if len(parts) == 4:
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1],
                        'author': parts[2],
                        'date': parts[3]
                    })

            return commits

        except subprocess.CalledProcessError:
            return []

    def get_diff(self, file_path: Optional[str] = None) -> str:
        """获取差异"""
        try:
            cmd = ["git", "diff"]
            if file_path:
                cmd.append(file_path)

            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""

    def create_commit_for_feature(self, feature_name: str, description: str) -> bool:
        """为功能创建提交

        Args:
            feature_name: 功能名称
            description: 功能描述

        Returns:
            是否成功
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[Feature] {feature_name}\n\n{description}\n\nTimestamp: {timestamp}\nCo-Authored-By: Infinity AI Agent"

        # 获取所有修改和新增的文件
        modified, untracked, staged = self.get_status()
        all_files = modified + untracked

        if not all_files and not staged:
            self.logger.info("No changes to commit")
            return True

        # 添加所有文件
        if not self.add_files(all_files):
            return False

        # 创建提交
        return self.commit(message)