import sys
import os
import time
import requests
from playwright.sync_api import sync_playwright
from browser import BrowserManager 

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def send_telegram(message, photo_path=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': message})
        if photo_path and os.path.exists(photo_path):
            with open(photo_path, 'rb') as f:
                requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", data={'chat_id': chat_id}, files={'photo': f})
    except Exception as e:
        print(f"Telegram 发送失败: {e}")

def run_automation():
    page = None
    try:
        with sync_playwright() as p:
            with BrowserManager(p) as context:
                page = context.new_page()
                page.set_viewport_size({"width": 1920, "height": 1080})
                
                print("访问目标页面...")
                page.goto("https://host2play.gratis/server/renew?i=0b2f82c5-df07-4457-a2d9-9d948ce3d12d")
                
                # --- 新增逻辑：立即截图 ---
                print("进行初始页面状态截图...")
                page.screenshot(path="initial_state.png", full_page=True)
                send_telegram("页面已打开，当前初始状态：", "initial_state.png")
                # -----------------------
                
                print("等待 renew 卡片显示...")
                page.wait_for_selector("#renew", state="visible", timeout=45000)
                
                print("点击 Renew server...")
                btn = page.get_by_role("button", name="Renew server")
                btn.wait_for(state="visible")
                btn.click()
                
                print("等待弹窗确认...")
                page.wait_for_selector(".swal2-confirm", timeout=15000)
                
                confirm_btn = page.get_by_role("button", name="Renew")
                confirm_btn.click(force=True)
                
                time.sleep(5)
                page.screenshot(path="result.png", full_page=True)
                send_telegram("Renew 操作成功完成！", "result.png")
                
    except Exception as e:
        error_msg = f"Renew 任务执行失败: {str(e)}"
        print(error_msg)
        if page:
            page.screenshot(path="error.png", full_page=True)
            send_telegram(error_msg, "error.png")
        else:
            send_telegram(error_msg)

if __name__ == "__main__":
    run_automation()
