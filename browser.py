import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from patchright.sync_api import BrowserContext, Playwright
from playwright_stealth import stealth_sync  # 引入反检测插件

load_dotenv()

BASE_DIR = Path(__file__).parent.absolute()
CHROME_PROFILE_DIR = BASE_DIR / ".chrome_profile"

class BrowserManager:
    def __init__(self, playwright: Playwright):
        self.playwright = playwright
        self._display = None
        self.context: Optional[BrowserContext] = None

    def __enter__(self) -> BrowserContext:
        # 暂时关闭虚拟环境显示，看是否是环境检测问题
        from xvfbwrapper import Xvfb
        self._display = Xvfb(width=1920, height=1080, colordepth=24)
        self._display.start()
        os.environ["DISPLAY"] = f":{self._display.new_display}"

        CHROME_PROFILE_DIR.mkdir(exist_ok=True)

        self.context = self.playwright.chromium.launch_persistent_context(
            str(CHROME_PROFILE_DIR),
            channel="chromium",
            headless=False,
            viewport={"width": 1920, "height": 1080},
            args=["--no-sandbox"], # 移除其他复杂参数
            env={**os.environ},
            proxy={"server": os.getenv("PROXY_SOCKS5")} if os.getenv("PROXY_SOCKS5") else None,
        )
        
        # 为每一个新建的页面注入 Stealth 伪装，消除自动化特征
        self.context.on("page", lambda page: stealth_sync(page))
        
        return self.context

    def __exit__(self, *_):
        if self.context:
            try: self.context.close()
            except: pass
        if self._display:
            try: self._display.stop()
            except: pass
