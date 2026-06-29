import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from patchright.sync_api import BrowserContext, Playwright

# 确保能找到同目录文件
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from nopecha import verify_api_key

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
        debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # 必须启动虚拟显示服务，否则 Linux 下无法运行 headed 浏览器
        if not debug:
            from xvfbwrapper import Xvfb
            self._display = Xvfb(width=1920, height=1080)
            self._display.start()
            os.environ["DISPLAY"] = f":{self._display.new_display}"

        CHROME_PROFILE_DIR.mkdir(exist_ok=True)

        launch_args = [
            "--no-sandbox",
            "--ozone-platform=x11",
            f"--load-extension={NOPECHA_EXTENSION_PATH}",
            f"--disable-extensions-except={NOPECHA_EXTENSION_PATH}",
        ]

        self.context = self.playwright.chromium.launch_persistent_context(
            str(CHROME_PROFILE_DIR),
            channel="chromium",
            headless=False,
            viewport={"width": 1920, "height": 1080},
            args=launch_args,
        )

        return self.context

    def __exit__(self, *_):
        if self.context:
            try:
                self.context.close()
            except Exception:
                pass
        if self._display:
            try:
                self._display.stop()
            except Exception:
                pass
