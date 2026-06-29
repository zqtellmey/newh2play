import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from patchright.sync_api import BrowserContext, Playwright

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
        # 必须恢复根据环境变量自动判断，不要写死 True
        debug = os.getenv("DEBUG", "false").lower() == "true"
        nopecha_enabled = os.getenv("NOPECHA_ENABLED", "true").lower() == "true"

        if nopecha_enabled:
            api_key = os.getenv("NOPECHA_API_KEY")
            if not api_key:
                raise EnvironmentError("NOPECHA_API_KEY is not set.")
            verify_api_key(api_key)

        if not debug:
            from xvfbwrapper import Xvfb
            self._display = Xvfb(width=1920, height=1080, colordepth=24)
            self._display.start()
            os.environ["DISPLAY"] = f":{self._display.new_display}"

        CHROME_PROFILE_DIR.mkdir(exist_ok=True)

        launch_args = [
            "--no-sandbox",
            "--ozone-platform=x11",
            "--disable-blink-features=AutomationControlled",
        ]
        if nopecha_enabled:
            launch_args += [
                f"--disable-extensions-except={NOPECHA_EXTENSION_PATH}",
                f"--load-extension={NOPECHA_EXTENSION_PATH}",
            ]

        proxy_url = os.getenv("PROXY_SOCKS5")
        proxy_config = {"server": proxy_url} if proxy_url else None

        # 启动持久化上下文
        self.context = self.playwright.chromium.launch_persistent_context(
            str(CHROME_PROFILE_DIR),
            channel="chromium",
            headless=False,
            viewport={"width": 1920, "height": 1080},
            args=launch_args,
            env={**os.environ},
            proxy=proxy_config,
        )

        if nopecha_enabled:
            self._inject_api_key(api_key)

        return self.context

    def __exit__(self, *_):
        if self.context:
            try: self.context.close()
            except: pass
        if self._display:
            try: self._display.stop()
            except: pass

    def _inject_api_key(self, api_key: str) -> None:
        page = self.context.new_page()
        try:
            page.goto(f"https://nopecha.com/setup#{api_key}", wait_until="load", timeout=10_000)
            page.wait_for_timeout(1000)
            if not page.get_by_text("Imported settings").is_visible():
                raise RuntimeError("NopeCHA key injection failed.")
        finally:
            page.close()
