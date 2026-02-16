"""
日志系统
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def get_logger(
    name: str = "infinity_ai",
    level: int = logging.INFO,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """获取日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径（可选）

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件处理器（如果指定）
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


class ProgressLogger:
    """进度日志记录器 - 专门用于记录到claude-progress.txt"""

    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self.logger = get_logger("progress")

    def log_action(self, action: str, details: str = ""):
        """记录Agent动作

        Args:
            action: 动作描述
            details: 详细信息
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {action}"
        if details:
            entry += f"\n  {details}"

        # 写入文件
        with open(self.progress_file, 'a', encoding='utf-8') as f:
            f.write(entry + "\n\n")

        self.logger.info(f"Progress logged: {action}")

    def log_session_start(self, session_id: str):
        """记录会话开始"""
        separator = "=" * 80
        self.log_action(
            f"SESSION START: {session_id}",
            separator
        )

    def log_session_end(self, session_id: str, summary: str):
        """记录会话结束"""
        self.log_action(
            f"SESSION END: {session_id}",
            f"Summary: {summary}\n{'=' * 80}"
        )
