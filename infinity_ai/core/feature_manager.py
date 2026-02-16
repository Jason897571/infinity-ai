"""
特性管理器 - 管理功能列表和状态
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from ..utils.file_manager import FileManager
from ..utils.logger import get_logger


class TestStep(BaseModel):
    """测试步骤"""
    description: str = Field(..., description="步骤描述")
    expected_result: Optional[str] = Field(None, description="预期结果")


class Feature(BaseModel):
    """功能特性"""
    id: str = Field(..., description="功能唯一ID")
    category: str = Field(default="functional", description="功能类别")
    description: str = Field(..., description="功能描述")
    priority: int = Field(default=1, ge=1, le=5, description="优先级 1-5，1最高")
    steps: List[str] = Field(default_factory=list, description="测试步骤")
    passes: bool = Field(default=False, description="是否通过测试")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = Field(None, description="完成时间")
    notes: Optional[str] = Field(None, description="备注")


class FeatureManager:
    """功能管理器"""

    def __init__(self, feature_file: Path):
        self.feature_file = feature_file
        self.file_manager = FileManager(Path.cwd())
        self.logger = get_logger("feature_manager")
        self.features: List[Feature] = []
        self._load_features()

    def _load_features(self):
        """从文件加载功能列表"""
        data = self.file_manager.read_json(self.feature_file)
        if data and 'features' in data:
            self.features = [Feature(**f) for f in data['features']]
            self.logger.info(f"Loaded {len(self.features)} features")
        else:
            self.features = []
            self.logger.info("No existing features found")

    def _save_features(self) -> bool:
        """保存功能列表到文件"""
        data = {
            'version': '1.0',
            'updated_at': datetime.now().isoformat(),
            'features': [f.model_dump() for f in self.features]
        }
        return self.file_manager.write_json(self.feature_file, data)

    def add_feature(
        self,
        description: str,
        steps: List[str],
        category: str = "functional",
        priority: int = 1
    ) -> Feature:
        """添加新功能

        Args:
            description: 功能描述
            steps: 测试步骤列表
            category: 功能类别
            priority: 优先级

        Returns:
            创建的功能对象
        """
        feature_id = f"feature_{len(self.features) + 1:03d}"

        feature = Feature(
            id=feature_id,
            category=category,
            description=description,
            priority=priority,
            steps=steps
        )

        self.features.append(feature)
        self._save_features()

        self.logger.info(f"Added feature: {feature_id} - {description}")
        return feature

    def get_feature(self, feature_id: str) -> Optional[Feature]:
        """获取功能"""
        for feature in self.features:
            if feature.id == feature_id:
                return feature
        return None

    def get_next_incomplete_feature(self) -> Optional[Feature]:
        """获取下一个未完成的功能（按优先级排序）

        Returns:
            优先级最高的未完成功能
        """
        incomplete = [f for f in self.features if not f.passes]
        if not incomplete:
            return None

        # 按优先级排序（数字越小优先级越高）
        incomplete.sort(key=lambda f: f.priority)
        return incomplete[0]

    def mark_feature_complete(self, feature_id: str, notes: Optional[str] = None) -> bool:
        """标记功能为完成

        Args:
            feature_id: 功能ID
            notes: 完成备注

        Returns:
            是否成功
        """
        feature = self.get_feature(feature_id)
        if not feature:
            self.logger.error(f"Feature not found: {feature_id}")
            return False

        feature.passes = True
        feature.completed_at = datetime.now().isoformat()
        feature.updated_at = datetime.now().isoformat()
        if notes:
            feature.notes = notes

        self._save_features()
        self.logger.info(f"Feature marked as complete: {feature_id}")
        return True

    def mark_feature_failed(self, feature_id: str, reason: str) -> bool:
        """标记功能为失败

        Args:
            feature_id: 功能ID
            reason: 失败原因

        Returns:
            是否成功
        """
        feature = self.get_feature(feature_id)
        if not feature:
            self.logger.error(f"Feature not found: {feature_id}")
            return False

        feature.passes = False
        feature.updated_at = datetime.now().isoformat()
        feature.notes = f"FAILED: {reason}"

        self._save_features()
        self.logger.warning(f"Feature marked as failed: {feature_id} - {reason}")
        return True

    def update_feature_steps(self, feature_id: str, steps: List[str]) -> bool:
        """更新功能的测试步骤"""
        feature = self.get_feature(feature_id)
        if not feature:
            return False

        feature.steps = steps
        feature.updated_at = datetime.now().isoformat()
        self._save_features()
        return True

    def get_progress_summary(self) -> Dict[str, Any]:
        """获取进度摘要

        Returns:
            {'total': int, 'completed': int, 'pending': int, 'percentage': float}
        """
        total = len(self.features)
        completed = sum(1 for f in self.features if f.passes)
        pending = total - completed

        return {
            'total': total,
            'completed': completed,
            'pending': pending,
            'percentage': (completed / total * 100) if total > 0 else 0.0
        }

    def list_features(self, category: Optional[str] = None) -> List[Feature]:
        """列出所有功能

        Args:
            category: 按类别过滤（可选）

        Returns:
            功能列表
        """
        if category:
            return [f for f in self.features if f.category == category]
        return self.features

    def clear_completed_features(self) -> int:
        """清除已完成的功能

        Returns:
            清除的功能数量
        """
        before = len(self.features)
        self.features = [f for f in self.features if not f.passes]
        after = len(self.features)

        removed = before - after
        if removed > 0:
            self._save_features()
            self.logger.info(f"Removed {removed} completed features")

        return removed

    def export_to_markdown(self) -> str:
        """导出为Markdown格式

        Returns:
            Markdown文本
        """
        lines = ["# Feature List\n"]

        summary = self.get_progress_summary()
        lines.append(f"## Progress: {summary['completed']}/{summary['total']} ({summary['percentage']:.1f}%)\n")

        for feature in self.features:
            status = "✓" if feature.passes else "○"
            lines.append(f"\n### {status} {feature.id} - {feature.description}\n")
            lines.append(f"- Category: {feature.category}")
            lines.append(f"- Priority: {feature.priority}")
            lines.append(f"- Status: {'PASSING' if feature.passes else 'FAILING'}")

            if feature.steps:
                lines.append("\n**Test Steps:**")
                for i, step in enumerate(feature.steps, 1):
                    lines.append(f"{i}. {step}")

            if feature.notes:
                lines.append(f"\n**Notes:** {feature.notes}")

            lines.append("")

        return "\n".join(lines)