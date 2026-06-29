import sys
import os
import time
import requests
from playwright.sync_api import sync_playwright
from browser import BrowserManager 

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def send_telegram(message, photo_path=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': message})
    if photo_path and os.path.exists(photo_path):
        with open(photo_path, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", data={'chat_id': chat_id}, files={'photo': f})

def run_automation():
    page = None
    try:
        with sync_playwright() as p:
            with BrowserManager(p) as context:
                page = context.new_page()
                # 恢复之前的基础视口
                page.set_viewport_size({"width": 1920, "height": 1080})
                
                print("访问页面...")
                page.goto("https://host2play.gratis/server/renew?i=0b2f82c5-df07-4457-a2d9-9d948ce3d12d")
                
                # 等待网络空闲
                page.wait_for_load_state("networkidle")
                
                # --- 仅在这里增加了一次截图，方便排查 ---
                page.screenshot(path="debug.png", full_page=True)
                send_telegram("页面已加载，当前状态：", "debug.png")
                # ------------------------------------

                print("点击 Renew server...")
                btn = page.get_by_role("button", name="Renew server")
                btn.wait_for(state="visible", timeout=30000)
                btn.click()
                
                print("等待弹窗...")
                page.wait_for_selector(".swal2-confirm", timeout=30000)
                page.get_by_role("button", name="Renew").click()
                
                send_telegram("Renew 操作成功！")
                
    except Exception as e:
        error_msg = f"错误: {str(e)}"
        print(error_msg)
        if page:
            page.screenshot(path="error.png", full_page=True)
            send_telegram(error_msg, "error.png")
        else:
            send_telegram(error_msg)

if __name__ == "__main__":
    run_automation()
