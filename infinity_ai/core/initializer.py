"""
初始化器Agent - 第一次会话运行，设置项目环境
"""
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from anthropic import Anthropic
from ..config.settings import Settings
from ..config.llm_config import LLMConfig
from ..utils.git_utils import GitManager
from ..utils.file_manager import FileManager
from ..utils.logger import get_logger
from .progress_tracker import ProgressTracker
from .feature_manager import FeatureManager


class InitializerAgent:
    """初始化器Agent

    在第一次会话运行，负责：
    1. 创建init.sh脚本
    2. 创建feature_list.json
    3. 创建claude-progress.txt
    4. 初始化Git仓库
    5. 创建初始提交
    """

    def __init__(
        self,
        project_root: Path,
        settings: Settings,
        llm_config: LLMConfig,
        project_requirements: str
    ):
        self.project_root = Path(project_root)
        self.settings = settings
        self.llm_config = llm_config
        self.project_requirements = project_requirements

        # 初始化工具
        self.git_manager = GitManager(self.project_root)
        self.file_manager = FileManager(self.project_root)
        self.progress_tracker = ProgressTracker(self.project_root / self.settings.progress_file)
        self.feature_manager = FeatureManager(self.project_root / self.settings.feature_list_file)

        # 初始化Claude客户端（支持 api_key 和 bearer 两种认证方式）
        self.client = Anthropic(**llm_config.get_client_kwargs())
        self.logger = get_logger("initializer")

        # 会话信息
        self.session_id = f"init_{uuid.uuid4().hex[:8]}"

    def initialize(self) -> bool:
        """执行完整的初始化流程

        Returns:
            是否成功
        """
        self.logger.info(f"Starting initialization session: {self.session_id}")
        self.progress_tracker.log_session_start(self.session_id, "initializer")

        try:
            # 1. 初始化Git仓库
            self.progress_tracker.log_action("Initializing Git repository")
            if not self.git_manager.init_repo():
                raise Exception("Failed to initialize Git repository")

            # 2. 分析项目需求，生成功能列表
            self.progress_tracker.log_action("Analyzing project requirements")
            features = self._analyze_requirements()
            if not features:
                raise Exception("Failed to generate feature list")

            # 3. 保存功能列表
            self.progress_tracker.log_action("Creating feature list file")
            for feature in features:
                self.feature_manager.add_feature(
                    description=feature['description'],
                    steps=feature['steps'],
                    category=feature.get('category', 'functional'),
                    priority=feature.get('priority', 1)
                )

            # 4. 创建init.sh脚本
            self.progress_tracker.log_action("Creating init.sh script")
            init_script = self._generate_init_script()
            self.file_manager.write_file(self.settings.init_script, init_script)
            self._make_script_executable(self.settings.init_script)

            # 5. 创建.gitignore（如果不存在）
            if not (self.project_root / ".gitignore").exists():
                self.progress_tracker.log_action("Creating .gitignore")
                self._create_gitignore()

            # 6. 创建初始Git提交
            self.progress_tracker.log_action("Creating initial commit")
            self.git_manager.add_files(["."])
            self.git_manager.commit(
                f"[Infinity AI] Initial project setup\n\n"
                f"- Created feature list with {len(features)} features\n"
                f"- Created init.sh startup script\n"
                f"- Created .gitignore\n\n"
                f"Session: {self.session_id}"
            )

            # 7. 生成项目摘要
            summary = self._generate_project_summary()

            self.progress_tracker.log_session_end(
                self.session_id,
                f"Initialization complete. {len(features)} features identified.",
                0
            )

            self.logger.info("Initialization completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            self.progress_tracker.log_error(str(e), "Initialization failed")
            return False

    def _analyze_requirements(self) -> List[Dict[str, Any]]:
        """使用Claude分析项目需求，生成功能列表

        Returns:
            功能列表
        """
        prompt = f"""
You are a software architect. Analyze the following project requirements and generate a comprehensive feature list.

Project Requirements:
{self.project_requirements}

For each feature, provide:
1. A clear description
2. Detailed test steps (how to verify the feature works)
3. Category (functional/ui/performance/security)
4. Priority (1=highest, 5=lowest)

Format your response as a JSON list:
[
  {{
    "description": "Feature description",
    "steps": ["Step 1", "Step 2", "Step 3"],
    "category": "functional",
    "priority": 1
  }},
  ...
]

Generate a comprehensive list of all features needed to complete this project.
"""

        try:
            self.logger.info(f"Calling API with model: {self.llm_config.model}")
            self.logger.debug(f"Prompt: {prompt[:200]}...")

            message = self.client.messages.create(
                model=self.llm_config.model,
                max_tokens=self.llm_config.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            # 提取JSON响应
            content = message.content[0].text
            self.logger.info(f"API response received, length: {len(content)}")
            self.logger.debug(f"Response content: {content[:500]}...")

            # 尝试解析JSON
            import json
            import re

            # 查找JSON数组
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                features = json.loads(json_match.group())
                self.logger.info(f"Successfully parsed {len(features)} features from response")
                return features
            else:
                self.logger.error("No valid JSON array found in response")
                self.logger.error(f"Full response: {content}")
                return []

        except Exception as e:
            self.logger.error(f"Failed to analyze requirements: {type(e).__name__}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    def _generate_init_script(self) -> str:
        """生成init.sh启动脚本

        Returns:
            脚本内容
        """
        # 尝试检测项目类型
        project_type = self._detect_project_type()

        if project_type == "node":
            return """#!/bin/bash
# Infinity AI - Development Server Startup Script

echo "Starting Node.js development server..."

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start development server
npm run dev
"""
        elif project_type == "python":
            return """#!/bin/bash
# Infinity AI - Development Server Startup Script

echo "Starting Python development server..."

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Start development server
python app.py
"""
        else:
            # 通用脚本
            return """#!/bin/bash
# Infinity AI - Development Server Startup Script

echo "Starting development environment..."

# Add your project-specific startup commands here
# Example:
# npm run dev
# or
# python app.py

echo "Development server is running!"
"""

    def _detect_project_type(self) -> str:
        """检测项目类型

        Returns:
            'node', 'python', or 'unknown'
        """
        if (self.project_root / "package.json").exists():
            return "node"
        elif (self.project_root / "requirements.txt").exists() or (self.project_root / "setup.py").exists():
            return "python"
        else:
            return "unknown"

    def _make_script_executable(self, script_path: Path):
        """使脚本可执行"""
        import os
        import stat

        full_path = self.project_root / script_path
        if full_path.exists():
            current_mode = os.stat(full_path).st_mode
            os.chmod(full_path, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            self.logger.info(f"Made script executable: {script_path}")

    def _create_gitignore(self):
        """创建.gitignore文件"""
        gitignore_content = """# Dependencies
node_modules/
venv/
__pycache__/
*.pyc

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
npm-debug.log*

# Environment
.env
.env.local

# Build
dist/
build/

# Testing
coverage/
.pytest_cache/

# Infinity AI specific
tests/screenshots/
*.backup
"""
        self.file_manager.write_file(".gitignore", gitignore_content)

    def _generate_project_summary(self) -> str:
        """生成项目摘要"""
        features = self.feature_manager.features
        summary = self.feature_manager.get_progress_summary()

        return f"""
Project Initialization Summary
{'=' * 60}

Project Root: {self.project_root}
Session ID: {self.session_id}

Features:
  Total: {summary['total']}
  Pending: {summary['pending']}

Files Created:
  - {self.settings.feature_list_file}
  - {self.settings.progress_file}
  - {self.settings.init_script}
  - .gitignore

Next Steps:
  1. Run 'bash {self.settings.init_script}' to start the dev server
  2. Run the coding agent to start implementing features
  3. Monitor progress in {self.settings.progress_file}

{'=' * 60}
"""

    def create_feature_from_template(
        self,
        template_type: str = "web_app"
    ) -> List[Dict[str, Any]]:
        """从模板创建功能列表

        Args:
            template_type: 模板类型

        Returns:
            功能列表
        """
        templates = {
            "web_app": [
                {
                    "description": "Homepage loads successfully",
                    "steps": [
                        "Navigate to homepage URL",
                        "Verify page title is correct",
                        "Verify main content is visible",
                        "Check that no console errors appear"
                    ],
                    "category": "functional",
                    "priority": 1
                },
                {
                    "description": "Navigation menu works correctly",
                    "steps": [
                        "Click on navigation menu",
                        "Verify menu items are displayed",
                        "Click each menu item",
                        "Verify correct page loads for each item"
                    ],
                    "category": "ui",
                    "priority": 2
                },
                {
                    "description": "User authentication works",
                    "steps": [
                        "Navigate to login page",
                        "Enter valid credentials",
                        "Click login button",
                        "Verify user is redirected to dashboard",
                        "Verify user is logged in"
                    ],
                    "category": "functional",
                    "priority": 1
                }
            ]
        }

        return templates.get(template_type, [])