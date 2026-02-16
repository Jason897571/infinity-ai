"""
全局配置管理
"""
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field
import json


class Settings(BaseModel):
    """全局配置设置"""

    # 项目路径
    project_root: Path = Field(default_factory=lambda: Path.cwd())

    # 进度文件路径
    progress_file: Path = Field(default_factory=lambda: Path("claude-progress.txt"))
    feature_list_file: Path = Field(default_factory=lambda: Path("feature_list.json"))
    init_script: Path = Field(default_factory=lambda: Path("init.sh"))

    # Agent配置
    max_context_windows: int = Field(default=100, description="最大上下文窗口数量")
    max_retries: int = Field(default=3, description="失败重试次数")

    # 测试配置
    browser_headless: bool = Field(default=True, description="浏览器是否无头模式")
    test_timeout: int = Field(default=30000, description="测试超时时间（毫秒）")

    # Git配置
    auto_commit: bool = Field(default=True, description="是否自动提交")
    commit_message_prefix: str = Field(default="[Infinity AI]", description="提交消息前缀")

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Settings":
        """从文件加载配置"""
        if config_path and config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return cls(**data)
        return cls()

    def save(self, config_path: Path):
        """保存配置到文件"""
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(mode='json'), f, indent=2, ensure_ascii=False)