"""
测试套件
"""
import pytest
from pathlib import Path
import tempfile
import shutil

from infinity_ai.core.feature_manager import FeatureManager, Feature
from infinity_ai.core.progress_tracker import ProgressTracker
from infinity_ai.config.settings import Settings
from infinity_ai.config.llm_config import LLMConfig


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def settings(temp_dir):
    """测试设置"""
    return Settings(project_root=temp_dir)


class TestFeatureManager:
    """功能管理器测试"""

    def test_add_feature(self, temp_dir):
        """测试添加功能"""
        feature_file = temp_dir / "feature_list.json"
        manager = FeatureManager(feature_file)

        feature = manager.add_feature(
            description="Test feature",
            steps=["Step 1", "Step 2"],
            category="functional",
            priority=1
        )

        assert feature.id == "feature_001"
        assert feature.description == "Test feature"
        assert len(feature.steps) == 2
        assert not feature.passes

    def test_get_next_incomplete_feature(self, temp_dir):
        """测试获取下一个未完成功能"""
        feature_file = temp_dir / "feature_list.json"
        manager = FeatureManager(feature_file)

        # 添加多个功能
        manager.add_feature("Feature 1", ["Step 1"], priority=2)
        manager.add_feature("Feature 2", ["Step 2"], priority=1)
        manager.add_feature("Feature 3", ["Step 3"], priority=1)

        # 标记第一个优先级1的功能为完成
        feature = manager.get_next_incomplete_feature()
        assert feature.description == "Feature 2"
        manager.mark_feature_complete(feature.id)

        # 下一个应该是Feature 3
        feature = manager.get_next_incomplete_feature()
        assert feature.description == "Feature 3"

    def test_mark_feature_complete(self, temp_dir):
        """测试标记功能完成"""
        feature_file = temp_dir / "feature_list.json"
        manager = FeatureManager(feature_file)

        feature = manager.add_feature("Test", ["Step"])
        assert not feature.passes

        manager.mark_feature_complete(feature.id)
        updated = manager.get_feature(feature.id)
        assert updated.passes
        assert updated.completed_at is not None

    def test_get_progress_summary(self, temp_dir):
        """测试进度摘要"""
        feature_file = temp_dir / "feature_list.json"
        manager = FeatureManager(feature_file)

        # 添加功能
        manager.add_feature("Feature 1", [])
        manager.add_feature("Feature 2", [])
        manager.add_feature("Feature 3", [])

        # 完成一个
        manager.mark_feature_complete("feature_001")

        summary = manager.get_progress_summary()
        assert summary['total'] == 3
        assert summary['completed'] == 1
        assert summary['pending'] == 2
        assert summary['percentage'] == pytest.approx(33.33, rel=0.01)

    def test_export_to_markdown(self, temp_dir):
        """测试导出为Markdown"""
        feature_file = temp_dir / "feature_list.json"
        manager = FeatureManager(feature_file)

        manager.add_feature("Feature 1", ["Step 1", "Step 2"])
        manager.mark_feature_complete("feature_001")

        markdown = manager.export_to_markdown()
        assert "# Feature List" in markdown
        assert "Feature 1" in markdown
        assert "PASSING" in markdown


class TestProgressTracker:
    """进度追踪器测试"""

    def test_log_session_start(self, temp_dir):
        """测试会话开始日志"""
        progress_file = temp_dir / "progress.txt"
        tracker = ProgressTracker(progress_file)

        tracker.log_session_start("test-session", "initializer")

        content = progress_file.read_text()
        assert "SESSION START" in content
        assert "test-session" in content
        assert "initializer" in content

    def test_log_action(self, temp_dir):
        """测试动作日志"""
        progress_file = temp_dir / "progress.txt"
        tracker = ProgressTracker(progress_file)

        tracker.log_action("Test action", "Test details")

        content = progress_file.read_text()
        assert "Test action" in content
        assert "Test details" in content

    def test_log_feature_complete(self, temp_dir):
        """测试功能完成日志"""
        progress_file = temp_dir / "progress.txt"
        tracker = ProgressTracker(progress_file)

        tracker.log_feature_complete("feature_001", True, "All tests passed")

        content = progress_file.read_text()
        assert "COMPLETED FEATURE" in content
        assert "feature_001" in content
        assert "PASSED" in content
        assert "All tests passed" in content

    def test_get_session_count(self, temp_dir):
        """测试获取会话次数"""
        progress_file = temp_dir / "progress.txt"
        tracker = ProgressTracker(progress_file)

        assert tracker.get_session_count() == 0

        tracker.log_session_start("session1", "initializer")
        assert tracker.get_session_count() == 1

        tracker.log_session_start("session2", "coding_agent")
        assert tracker.get_session_count() == 2


class TestSettings:
    """设置测试"""

    def test_default_settings(self):
        """测试默认设置"""
        settings = Settings()

        assert settings.max_context_windows == 100
        assert settings.max_retries == 3
        assert settings.browser_headless is True
        assert settings.auto_commit is True

    def test_save_and_load(self, temp_dir):
        """测试保存和加载设置"""
        config_file = temp_dir / "config.json"

        # 创建并保存设置
        settings1 = Settings(project_root=temp_dir)
        settings1.max_context_windows = 200
        settings1.save(config_file)

        # 加载设置
        settings2 = Settings.load(config_file)
        assert settings2.max_context_windows == 200


class TestLLMConfig:
    """LLM配置测试"""

    def test_api_key_from_env(self, monkeypatch):
        """测试从环境变量读取API密钥"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test123")

        config = LLMConfig()
        assert config.api_key == "sk-ant-test123"

    def test_is_valid(self, monkeypatch):
        """测试配置验证"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test123")

        config = LLMConfig()
        assert config.is_valid()

    def test_invalid_api_key_format(self):
        """测试无效的API密钥格式"""
        with pytest.raises(ValueError):
            LLMConfig(api_key="invalid-key")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])