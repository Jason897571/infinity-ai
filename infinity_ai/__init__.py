"""
Infinity AI - 无限运行的AI Agent框架
基于Anthropic的"Effective Harnesses for Long-Running Agents"设计
"""

__version__ = "0.1.0"
__author__ = "Jason Gu"

from .core.initializer import InitializerAgent
from .core.coding_agent import CodingAgent
from .core.scheduler import AgentScheduler
from .core.feature_manager import FeatureManager
from .core.progress_tracker import ProgressTracker

__all__ = [
    "InitializerAgent",
    "CodingAgent",
    "AgentScheduler",
    "FeatureManager",
    "ProgressTracker",
]