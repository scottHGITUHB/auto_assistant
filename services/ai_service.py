import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

class AIService:
    def __init__(self):
        self.ai_web_url = os.getenv("AI_WEB_URL", "https://chat.openai.com")
        self.ai_username = os.getenv("AI_USERNAME")
        self.ai_password = os.getenv("AI_PASSWORD")
        self.ai_timeout = int(os.getenv("AI_TIMEOUT", "30000"))
    
    def get_ai_answer(self, question):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # 访问AI网站
                page.goto(self.ai_web_url, timeout=self.ai_timeout)
                
                # 这里需要根据具体的AI网站进行登录和操作
                # 例如ChatGPT的登录流程
                if self.ai_username and self.ai_password:
                    # 点击登录按钮
                    page.click("button:has-text('Log in')", timeout=10000)
                    
                    # 输入用户名
                    page.fill("input[type='email']", self.ai_username)
                    page.click("button:has-text('Continue')")
                    
                    # 输入密码
                    page.fill("input[type='password']", self.ai_password)
                    page.click("button:has-text('Log in')")
                    
                    # 等待登录完成
                    page.wait_for_load_state("networkidle", timeout=self.ai_timeout)
                
                # 输入问题
                page.fill("textarea", question)
                page.press("textarea", "Enter")
                
                # 等待回答生成
                page.wait_for_selector(".markdown", timeout=self.ai_timeout)
                
                # 获取回答
                answer = page.inner_text(".markdown")
                
                browser.close()
                return answer
        except Exception as e:
            return f"获取AI回答失败: {str(e)}"

ai_service = AIService()
