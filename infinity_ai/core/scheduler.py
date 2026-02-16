"""
Agent调度器 - 管理Agent的运行和会话
"""
import time
import signal
import sys
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime
from enum import Enum

from .initializer import InitializerAgent
from .coding_agent import CodingAgent
from .feature_manager import FeatureManager
from .progress_tracker import ProgressTracker
from ..config.settings import Settings
from ..config.llm_config import LLMConfig
from ..utils.logger import get_logger


class SchedulerState(Enum):
    """调度器状态"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"


class AgentScheduler:
    """Agent调度器

    负责管理整个框架的运行：
    1. 检查是否需要初始化
    2. 决定运行哪个Agent
    3. 管理会话生命周期
    4. 处理错误和重试
    """

    def __init__(
        self,
        project_root: Path,
        settings: Settings,
        llm_config: LLMConfig,
        project_requirements: Optional[str] = None
    ):
        self.project_root = Path(project_root)
        self.settings = settings
        self.llm_config = llm_config
        self.project_requirements = project_requirements

        # 初始化工具
        self.feature_manager = FeatureManager(self.project_root / self.settings.feature_list_file)
        self.progress_tracker = ProgressTracker(self.project_root / self.settings.progress_file)
        self.logger = get_logger("scheduler")

        # 状态管理
        self.state = SchedulerState.IDLE
        self.iteration_count = 0
        self.running = True

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """处理中断信号"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        self.state = SchedulerState.STOPPED
        sys.exit(0)

    def run(self, mode: str = "continuous"):
        """运行调度器

        Args:
            mode: 运行模式
                - "continuous": 连续运行，直到所有功能完成
                - "single": 只运行一个会话
                - "interactive": 每次会话后暂停，等待用户确认
        """
        self.logger.info(f"Starting scheduler in {mode} mode")
        self.running = True

        try:
            # 检查是否需要初始化
            if self._needs_initialization():
                self.state = SchedulerState.INITIALIZING
                if not self._run_initialization():
                    self.logger.error("Initialization failed, stopping scheduler")
                    self.state = SchedulerState.STOPPED
                    return

            # 运行编码Agent
            self.state = SchedulerState.RUNNING

            if mode == "single":
                self._run_single_session()
            elif mode == "interactive":
                self._run_interactive()
            else:  # continuous
                self._run_continuous()

        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")
            self.state = SchedulerState.STOPPED
            raise

    def _needs_initialization(self) -> bool:
        """检查是否需要初始化

        Returns:
            True如果需要初始化
        """
        # 检查关键文件是否存在
        feature_file = self.project_root / self.settings.feature_list_file
        progress_file = self.project_root / self.settings.progress_file

        if not feature_file.exists() or not progress_file.exists():
            self.logger.info("Initialization files not found, initialization needed")
            return True

        # 检查功能列表是否为空
        if not self.feature_manager.features:
            self.logger.info("Feature list is empty, initialization needed")
            return True

        return False

    def _run_initialization(self) -> bool:
        """运行初始化

        Returns:
            是否成功
        """
        self.logger.info("Running initialization...")

        if not self.project_requirements:
            self.logger.error("Project requirements not provided for initialization")
            return False

        initializer = InitializerAgent(
            self.project_root,
            self.settings,
            self.llm_config,
            self.project_requirements
        )

        success = initializer.initialize()

        if success:
            self.logger.info("Initialization completed successfully")
            # 重新加载功能管理器
            self.feature_manager = FeatureManager(self.project_root / self.settings.feature_list_file)
        else:
            self.logger.error("Initialization failed")

        return success

    def _run_single_session(self):
        """运行单个会话"""
        self.logger.info("Running single session")

        agent = CodingAgent(self.project_root, self.settings, self.llm_config)
        success = agent.run_session()

        if success:
            self.logger.info("Session completed successfully")
        else:
            self.logger.warning("Session failed")

        self.state = SchedulerState.COMPLETED

    def _run_interactive(self):
        """交互式运行 - 每次会话后等待用户确认"""
        self.logger.info("Running in interactive mode")

        while self.running:
            # 检查是否还有未完成的功能
            summary = self.feature_manager.get_progress_summary()
            if summary['pending'] == 0:
                self.logger.info("All features completed!")
                self.state = SchedulerState.COMPLETED
                break

            # 运行一个会话
            agent = CodingAgent(self.project_root, self.settings, self.llm_config)
            success = agent.run_session()

            self.iteration_count += 1
            self.logger.info(f"Session {self.iteration_count} {'succeeded' if success else 'failed'}")

            # 等待用户确认
            try:
                input("\nPress Enter to continue, or Ctrl+C to stop...")
            except KeyboardInterrupt:
                self.logger.info("User interrupted")
                self.state = SchedulerState.STOPPED
                break

            # 重新加载功能管理器
            self.feature_manager = FeatureManager(self.project_root / self.settings.feature_list_file)

    def _run_continuous(self):
        """连续运行 - 直到所有功能完成或达到最大迭代次数"""
        self.logger.info("Running in continuous mode")

        max_iterations = self.settings.max_context_windows
        consecutive_failures = 0
        max_consecutive_failures = 3

        while self.running and self.iteration_count < max_iterations:
            # 检查是否还有未完成的功能
            summary = self.feature_manager.get_progress_summary()
            if summary['pending'] == 0:
                self.logger.info("All features completed!")
                self.state = SchedulerState.COMPLETED
                break

            # 运行一个会话
            agent = CodingAgent(self.project_root, self.settings, self.llm_config)
            success = agent.run_session()

            self.iteration_count += 1

            if success:
                consecutive_failures = 0
                self.logger.info(
                    f"Session {self.iteration_count} succeeded. "
                    f"Progress: {summary['completed']}/{summary['total']} features"
                )
            else:
                consecutive_failures += 1
                self.logger.warning(
                    f"Session {self.iteration_count} failed. "
                    f"Consecutive failures: {consecutive_failures}/{max_consecutive_failures}"
                )

                # 如果连续失败太多，暂停
                if consecutive_failures >= max_consecutive_failures:
                    self.logger.error(
                        f"Too many consecutive failures ({consecutive_failures}). "
                        f"Pausing scheduler."
                    )
                    self.state = SchedulerState.PAUSED

                    # 等待一段时间再重试
                    time.sleep(30)
                    consecutive_failures = 0
                    self.state = SchedulerState.RUNNING

            # 重新加载功能管理器
            self.feature_manager = FeatureManager(self.project_root / self.settings.feature_list_file)

            # 短暂休息
            time.sleep(2)

        if self.iteration_count >= max_iterations:
            self.logger.info(f"Reached maximum iterations: {max_iterations}")
            self.state = SchedulerState.COMPLETED

    def get_status(self) -> dict:
        """获取调度器状态

        Returns:
            状态信息字典
        """
        feature_summary = self.feature_manager.get_progress_summary()
        progress_summary = self.progress_tracker.generate_summary()

        return {
            'state': self.state.value,
            'iteration_count': self.iteration_count,
            'features': feature_summary,
            'sessions': progress_summary['total_sessions'],
            'features_completed': progress_summary['total_features_completed']
        }

    def pause(self):
        """暂停调度器"""
        self.state = SchedulerState.PAUSED
        self.logger.info("Scheduler paused")

    def resume(self):
        """恢复调度器"""
        self.state = SchedulerState.RUNNING
        self.logger.info("Scheduler resumed")

    def stop(self):
        """停止调度器"""
        self.running = False
        self.state = SchedulerState.STOPPED
        self.logger.info("Scheduler stopped")