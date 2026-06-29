import os
import time
import requests
from playwright.sync_api import sync_playwright
from browser import BrowserManager 

def send_telegram(message, photo_path=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': message})
        if photo_path and os.path.exists(photo_path):
            with open(photo_path, 'rb') as f:
                requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", data={'chat_id': chat_id}, files={'photo': f})
    except: pass

def run_automation():
    try:
        with sync_playwright() as p:
            with BrowserManager(p) as context:
                page = context.new_page()
                page.set_viewport_size({"width": 1280, "height": 720})
                
                print("访问目标页面...")
                page.goto("https://host2play.gratis/server/renew?i=0b2f82c5-df07-4457-a2d9-9d948ce3d12d")
                time.sleep(5) # 等待初始加载

                # --- 核心移植：暴力清理阻碍元素 ---
                print("清理阻碍元素...")
                page.evaluate("""() => {
                    const selectors = ['ins.adsbygoogle', 'iframe[src*="ads"]', '.modal-backdrop', '[id*="consent"]', '[class*="consent"]', '.loading-spinner'];
                    selectors.forEach(sel => {
                        document.querySelectorAll(sel).forEach(el => el.remove());
                    });
                }""")
                # --------------------------------

                print("等待 Renew 卡片...")
                page.wait_for_selector("#renew", state="visible", timeout=20000)
                
                print("点击 Renew...")
                page.get_by_role("button", name="Renew server").click()
                
                time.sleep(5)
                page.screenshot(path="final.png")
                send_telegram("操作成功！", "final.png")
                
    except Exception as e:
        print(f"出错: {e}")
        send_telegram(f"失败: {str(e)}")

if __name__ == "__main__":
    run_automation()
