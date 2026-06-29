import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from patchright.sync_api import BrowserContext, Playwright

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

BASE_DIR = Path(__file__).parent.absolute()
NOPECHA_EXTENSION_PATH = BASE_DIR / "extensions" / "nopecha"
CHROME_PROFILE_DIR = BASE_DIR / ".chrome_profile"

class BrowserManager:
    def __init__(self, playwright: Playwright):
        self.playwright = playwright
        self._display = None
        self.context: Optional[BrowserContext] = None

    def __enter__(self) -> BrowserContext:
        # 强制启用 Xvfb，这是在 GitHub Actions 运行 headed 模式的唯一方式
        from xvfbwrapper import Xvfb
        self._display = Xvfb(width=1920, height=1080)
        self._display.start()
        
        # 显式设置环境变量
        os.environ["DISPLAY"] = f":{self._display.new_display}"
        print(f"Xvfb 已启动，显示器 ID: {os.environ['DISPLAY']}")

        CHROME_PROFILE_DIR.mkdir(exist_ok=True)

        # 启动参数保持精简但包含插件
        launch_args = [
            "--no-sandbox",
            "--ozone-platform=x11",
            f"--load-extension={NOPECHA_EXTENSION_PATH}",
            f"--disable-extensions-except={NOPECHA_EXTENSION_PATH}",
        ]

        self.context = self.playwright.chromium.launch_persistent_context(
            str(CHROME_PROFILE_DIR),
            channel="chromium",
            headless=False,  # 必须为 False 才能加载插件
            viewport={"width": 1920, "height": 1080},
            args=launch_args,
        )
        return self.context

    def __exit__(self, *_):
        if self.context:
            try: self.context.close()
            except: pass
        if self._display:
            try: self._display.stop()
            except: pass
