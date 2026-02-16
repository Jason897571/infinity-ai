"""
浏览器自动化测试工具
基于Puppeteer/Playway进行端到端测试
"""
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from .logger import get_logger


class BrowserTester:
    """浏览器测试器

    使用Playwright或Puppeteer进行端到端测试
    """

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
        test_script_path: Optional[Path] = None
    ):
        self.headless = headless
        self.timeout = timeout
        self.test_script_path = test_script_path or Path("tests/browser")
        self.logger = get_logger("browser_tester")

    def check_playwright_installed(self) -> bool:
        """检查Playwright是否已安装"""
        try:
            result = subprocess.run(
                ["npx", "playwright", "--version"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    async def run_test_script(self, script_path: Path) -> Dict[str, Any]:
        """运行测试脚本

        Args:
            script_path: 测试脚本路径

        Returns:
            {'success': bool, 'output': str, 'error': str}
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                "node", str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.timeout / 1000
            )

            return {
                'success': proc.returncode == 0,
                'output': stdout.decode('utf-8'),
                'error': stderr.decode('utf-8')
            }

        except asyncio.TimeoutError:
            return {
                'success': False,
                'output': '',
                'error': f'Test timed out after {self.timeout}ms'
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }

    def test_feature(self, test_steps: List[str]) -> Dict[str, Any]:
        """测试功能

        Args:
            test_steps: 测试步骤列表，如 ["Navigate to /", "Click #new-chat", "Verify .chat-area"]

        Returns:
            测试结果
        """
        # 生成测试脚本
        script = self._generate_test_script(test_steps)
        script_path = self.test_script_path / f"test_{hash(tuple(test_steps))}.js"

        # 保存测试脚本
        script_path.parent.mkdir(parents=True, exist_ok=True)
        with open(script_path, 'w') as f:
            f.write(script)

        self.logger.info(f"Generated test script: {script_path}")

        # 运行测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.run_test_script(script_path))
            return result
        finally:
            loop.close()

    def _generate_test_script(self, test_steps: List[str]) -> str:
        """生成Playwright测试脚本

        Args:
            test_steps: 测试步骤列表

        Returns:
            JavaScript测试代码
        """
        steps_code = []
        for i, step in enumerate(test_steps):
            steps_code.append(f"  // Step {i+1}: {step}")
            steps_code.append(f"  {self._parse_test_step(step)}")

        steps_code_str = "\n".join(steps_code)

        return f"""
const {{ chromium }} = require('playwright');

(async () => {{
  const browser = await chromium.launch({{ headless: {str(self.headless).lower()} }});
  const page = await browser.newPage();

  try {{
{steps_code_str}

    console.log('All tests passed!');
    process.exit(0);
  }} catch (error) {{
    console.error('Test failed:', error.message);
    process.exit(1);
  }} finally {{
    await browser.close();
  }}
}})();
"""

    def _parse_test_step(self, step: str) -> str:
        """解析测试步骤为Playwright代码

        Args:
            step: 测试步骤描述

        Returns:
            Playwright代码
        """
        step_lower = step.lower()

        # 导航操作
        if 'navigate to' in step_lower or 'go to' in step_lower:
            url = step.split()[-1]
            return f'await page.goto("{url}");'

        # 点击操作
        if 'click' in step_lower:
            selector = step.split()[-1]
            return f'await page.click("{selector}");'

        # 输入操作
        if 'type' in step_lower or 'enter' in step_lower or 'input' in step_lower:
            parts = step.split()
            text = parts[-1].strip('"\'')
            selector = parts[-2] if len(parts) > 1 else 'input'
            return f'await page.fill("{selector}", "{text}");'

        # 验证操作
        if 'verify' in step_lower or 'check' in step_lower or 'assert' in step_lower:
            selector = step.split()[-1]
            return f'await page.waitForSelector("{selector}", {{ timeout: {self.timeout} }});'

        # 等待操作
        if 'wait' in step_lower:
            if 'second' in step_lower:
                seconds = int([s for s in step.split() if s.isdigit()][0])
                return f'await page.waitForTimeout({seconds * 1000});'
            return f'await page.waitForTimeout(1000);'

        # 默认：等待元素
        selector = step.split()[-1]
        return f'await page.waitForSelector("{selector}", {{ timeout: {self.timeout} }});'

    def create_basic_e2e_test(self, base_url: str = "http://localhost:3000") -> str:
        """创建基本的端到端测试脚本

        Returns:
            测试脚本路径
        """
        script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
  const browser = await chromium.launch({{ headless: {str(self.headless).lower()} }});
  const page = await browser.newPage();

  try {{
    console.log('Testing basic functionality...');

    // 导航到主页
    await page.goto('{base_url}');
    console.log('✓ Homepage loaded');

    // 等待主要内容加载
    await page.waitForSelector('body', {{ timeout: {self.timeout} }});

    // 截图
    await page.screenshot({{ path: 'tests/screenshots/basic-test.png' }});

    console.log('✓ All basic tests passed!');
    process.exit(0);
  }} catch (error) {{
    console.error('✗ Test failed:', error.message);
    await page.screenshot({{ path: 'tests/screenshots/error.png' }});
    process.exit(1);
  }} finally {{
    await browser.close();
  }}
}})();
"""

        script_path = self.test_script_path / "basic-e2e.js"
        script_path.parent.mkdir(parents=True, exist_ok=True)

        with open(script_path, 'w') as f:
            f.write(script)

        self.logger.info(f"Created basic E2E test: {script_path}")
        return str(script_path)