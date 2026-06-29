import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from patchright.sync_api import BrowserContext, Playwright

load_dotenv()

BASE_DIR = Path(__file__).parent.absolute()
CHROME_PROFILE_DIR = BASE_DIR / ".chrome_profile"

class BrowserManager:
    def __init__(self, playwright: Playwright):
        self.playwright = playwright
        self._display = None
        self.context: Optional[BrowserContext] = None

    def __enter__(self) -> BrowserContext:
        from xvfbwrapper import Xvfb
        self._display = Xvfb(width=1920, height=1080, colordepth=24)
        self._display.start()
        os.environ["DISPLAY"] = f":{self._display.new_display}"

        CHROME_PROFILE_DIR.mkdir(exist_ok=True)

        # 对齐 mcscrap 的简洁启动逻辑
        self.context = self.playwright.chromium.launch_persistent_context(
            str(CHROME_PROFILE_DIR),
            channel="chromium",
            headless=False,
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            proxy={"server": os.getenv("PROXY_SOCKS5")} if os.getenv("PROXY_SOCKS5") else None,
        )
        
        # 使用 mcscrap 风格的初始化脚本，彻底抹除自动化标识
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.navigator.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
        """)
        
        return self.context

    def __exit__(self, *_):
        if self.context:
            try: self.context.close()
            except: pass
        if self._display:
            try: self._display.stop()
            except: pass
