"""
命令行接口 - Infinity AI Framework CLI
"""
import click
from pathlib import Path
from typing import Optional
import json

from dotenv import load_dotenv

from .core.scheduler import AgentScheduler


def _load_env_file():
    """从当前目录及父目录加载 .env 文件"""
    path = Path.cwd()
    for _ in range(5):  # 最多向上查找5层
        env_file = path / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            break
        parent = path.parent
        if parent == path:
            break
        path = parent
    else:
        load_dotenv()  # 回退到默认行为（cwd）
from .config.settings import Settings
from .config.llm_config import LLMConfig
from .utils.logger import get_logger


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """Infinity AI - 无限运行的AI Agent框架"""
    _load_env_file()


@cli.command()
@click.option('--project-root', '-p', default='.', help='项目根目录')
@click.option('--requirements', '-r', required=True, help='项目需求描述文件路径')
@click.option('--config', '-c', help='配置文件路径')
def init(project_root: str, requirements: str, config: Optional[str]):
    """初始化项目 - 创建必要的文件和结构"""

    logger = get_logger("cli")

    # 读取项目需求
    req_path = Path(requirements)
    if not req_path.exists():
        logger.error(f"Requirements file not found: {requirements}")
        return

    with open(req_path, 'r', encoding='utf-8') as f:
        project_requirements = f.read()

    # 加载配置
    settings = Settings.load(Path(config) if config else None)
    settings.project_root = Path(project_root)

    # 加载LLM配置
    llm_config = LLMConfig()
    if not llm_config.is_valid():
        logger.error("Invalid LLM configuration. Please set ANTHROPIC_API_KEY environment variable.")
        return

    # 运行调度器（只执行初始化）
    scheduler = AgentScheduler(
        Path(project_root),
        settings,
        llm_config,
        project_requirements
    )

    # 执行初始化
    success = scheduler._run_initialization()
    if success:
        logger.info("Project initialized successfully!")
    else:
        logger.error("Project initialization failed!")
        raise SystemExit(1)


@cli.command()
@click.option('--project-root', '-p', default='.', help='项目根目录')
@click.option('--mode', '-m',
              type=click.Choice(['continuous', 'single', 'interactive']),
              default='continuous',
              help='运行模式')
@click.option('--requirements', '-r', help='项目需求描述文件路径（初始化时需要，默认尝试 requirements.txt）')
@click.option('--config', '-c', help='配置文件路径')
def run(project_root: str, mode: str, requirements: Optional[str], config: Optional[str]):
    """运行AI Agent - 自动完成任务"""

    logger = get_logger("cli")

    # 加载配置
    settings = Settings.load(Path(config) if config else None)
    project_path = Path(project_root)
    settings.project_root = project_path

    # 加载LLM配置
    llm_config = LLMConfig()
    if not llm_config.is_valid():
        logger.error("Invalid LLM configuration. Please set ANTHROPIC_API_KEY environment variable.")
        return

    # 读取项目需求（初始化时需要）
    project_requirements = None
    if requirements:
        req_path = Path(requirements)
        if not req_path.is_absolute():
            req_path = project_path / req_path
        if req_path.exists():
            with open(req_path, 'r', encoding='utf-8') as f:
                project_requirements = f.read()
        else:
            logger.error(f"Requirements file not found: {req_path}")
            raise SystemExit(1)
    else:
        # 未指定时，尝试从项目根目录读取 requirements.txt
        default_req = project_path / "requirements.txt"
        if default_req.exists():
            with open(default_req, 'r', encoding='utf-8') as f:
                project_requirements = f.read()

    # 运行调度器
    scheduler = AgentScheduler(
        project_path,
        settings,
        llm_config,
        project_requirements
    )

    scheduler.run(mode=mode)


@cli.command()
@click.option('--project-root', '-p', default='.', help='项目根目录')
def status(project_root: str):
    """查看项目状态 - 显示进度和统计信息"""

    logger = get_logger("cli")

    # 加载配置
    settings = Settings(project_root=Path(project_root))

    # 检查文件是否存在
    feature_file = Path(project_root) / settings.feature_list_file
    progress_file = Path(project_root) / settings.progress_file

    if not feature_file.exists():
        logger.info("Project not initialized. Run 'infinity-ai init' first.")
        return

    # 加载功能管理器和进度追踪器
    from .core.feature_manager import FeatureManager
    from .core.progress_tracker import ProgressTracker

    feature_manager = FeatureManager(feature_file)
    progress_tracker = ProgressTracker(progress_file)

    # 获取状态
    feature_summary = feature_manager.get_progress_summary()
    progress_summary = progress_tracker.generate_summary()

    # 显示状态
    click.echo("\n" + "=" * 60)
    click.echo("INFINITY AI - PROJECT STATUS")
    click.echo("=" * 60)

    click.echo(f"\nProject Root: {Path(project_root).absolute()}")

    click.echo("\n📊 Features:")
    click.echo(f"  Total:      {feature_summary['total']}")
    click.echo(f"  Completed:  {feature_summary['completed']}")
    click.echo(f"  Pending:    {feature_summary['pending']}")
    click.echo(f"  Progress:   {feature_summary['percentage']:.1f}%")

    click.echo("\n📈 Sessions:")
    click.echo(f"  Total Sessions: {progress_summary['total_sessions']}")
    click.echo(f"  Features Completed: {progress_summary['total_features_completed']}")

    # 显示待处理的功能
    next_feature = feature_manager.get_next_incomplete_feature()
    if next_feature:
        click.echo(f"\n🎯 Next Feature:")
        click.echo(f"  ID: {next_feature.id}")
        click.echo(f"  Description: {next_feature.description}")
        click.echo(f"  Priority: {next_feature.priority}")

    click.echo("\n" + "=" * 60 + "\n")


@cli.command()
@click.option('--project-root', '-p', default='.', help='项目根目录')
@click.option('--output', '-o', default='feature_report.md', help='输出文件名')
def report(project_root: str, output: str):
    """生成报告 - 导出功能列表和进度"""

    logger = get_logger("cli")

    # 加载配置
    settings = Settings(project_root=Path(project_root))

    # 加载功能管理器
    feature_file = Path(project_root) / settings.feature_list_file
    from .core.feature_manager import FeatureManager
    feature_manager = FeatureManager(feature_file)

    # 导出为Markdown
    markdown = feature_manager.export_to_markdown()

    # 写入文件
    output_path = Path(output)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    click.echo(f"Report generated: {output_path.absolute()}")


@cli.command()
@click.option('--project-root', '-p', default='.', help='项目根目录')
@click.argument('description')
@click.option('--steps', '-s', multiple=True, help='测试步骤')
@click.option('--category', default='functional', help='功能类别')
@click.option('--priority', default=1, type=int, help='优先级 (1-5)')
def add_feature(
    project_root: str,
    description: str,
    steps: tuple,
    category: str,
    priority: int
):
    """添加新功能 - 手动添加功能到列表"""

    logger = get_logger("cli")

    # 加载配置
    settings = Settings(project_root=Path(project_root))

    # 加载功能管理器
    feature_file = Path(project_root) / settings.feature_list_file
    from .core.feature_manager import FeatureManager
    feature_manager = FeatureManager(feature_file)

    # 添加功能
    feature = feature_manager.add_feature(
        description=description,
        steps=list(steps) if steps else [],
        category=category,
        priority=priority
    )

    click.echo(f"Feature added: {feature.id} - {feature.description}")


@cli.command()
@click.option('--project-root', '-p', default='.', help='项目根目录')
@click.argument('feature-id')
def complete_feature(project_root: str, feature_id: str):
    """标记功能为完成"""

    logger = get_logger("cli")

    # 加载配置
    settings = Settings(project_root=Path(project_root))

    # 加载功能管理器
    feature_file = Path(project_root) / settings.feature_list_file
    from .core.feature_manager import FeatureManager
    feature_manager = FeatureManager(feature_file)

    # 标记完成
    if feature_manager.mark_feature_complete(feature_id):
        click.echo(f"Feature marked as complete: {feature_id}")
    else:
        click.echo(f"Feature not found: {feature_id}", err=True)


@cli.command()
def config():
    """显示当前配置"""
    settings = Settings()

    click.echo("\n" + "=" * 60)
    click.echo("INFINITY AI - CONFIGURATION")
    click.echo("=" * 60 + "\n")

    click.echo(f"Project Root: {settings.project_root}")
    click.echo(f"Progress File: {settings.progress_file}")
    click.echo(f"Feature List File: {settings.feature_list_file}")
    click.echo(f"Init Script: {settings.init_script}")
    click.echo(f"Max Context Windows: {settings.max_context_windows}")
    click.echo(f"Max Retries: {settings.max_retries}")
    click.echo(f"Browser Headless: {settings.browser_headless}")
    click.echo(f"Test Timeout: {settings.test_timeout}ms")
    click.echo(f"Auto Commit: {settings.auto_commit}")

    click.echo("\n" + "=" * 60 + "\n")


if __name__ == '__main__':
    cli()