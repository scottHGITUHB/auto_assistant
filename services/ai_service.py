import os
import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import logging

load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.ai_web_url = os.getenv("AI_WEB_URL", "https://chat.openai.com")
        self.ai_username = os.getenv("AI_USERNAME")
        self.ai_password = os.getenv("AI_PASSWORD")
        self.ai_timeout = int(os.getenv("AI_TIMEOUT", "15000"))  # 改为15秒超时
        self.session_cache = {}  # 内存级会话缓存
        self.semaphore = asyncio.Semaphore(5)  # 并发限制，最多5个并行请求
    
    async def get_ai_answer(self, question, user_id=None):
        # 使用并发锁限制并行请求
        async with self.semaphore:
            try:
                # 超时控制
                async with asyncio.timeout(self.ai_timeout / 1000):
                    async with async_playwright() as p:
                        browser = await p.chromium.launch(headless=True)
                        try:
                            page = await browser.new_page()
                            
                            # 访问AI网站
                            await page.goto(self.ai_web_url, timeout=self.ai_timeout)
                            
                            # 登录流程
                            if self.ai_username and self.ai_password:
                                try:
                                    # 点击登录按钮
                                    await page.click("button:has-text('Log in')", timeout=5000)
                                    
                                    # 输入用户名
                                    await page.fill("input[type='email']", self.ai_username)
                                    await page.click("button:has-text('Continue')", timeout=5000)
                                    
                                    # 输入密码
                                    await page.fill("input[type='password']", self.ai_password)
                                    await page.click("button:has-text('Log in')", timeout=5000)
                                    
                                    # 等待登录完成
                                    await page.wait_for_load_state("networkidle", timeout=self.ai_timeout)
                                except Exception as login_error:
                                    logger.warning(f"登录失败，使用游客模式: {login_error}")
                            
                            # 处理会话上下文
                            if user_id and user_id in self.session_cache:
                                # 恢复会话历史
                                history = self.session_cache[user_id]
                                # 这里可以根据具体AI网站的API恢复会话
                            
                            # 输入问题
                            await page.fill("textarea", question)
                            await page.press("textarea", "Enter")
                            
                            # 等待回答生成
                            await page.wait_for_selector(".markdown", timeout=self.ai_timeout)
                            
                            # 获取回答
                            answer = await page.inner_text(".markdown")
                            
                            # 更新会话缓存
                            if user_id:
                                self.session_cache[user_id] = {
                                    "question": question,
                                    "answer": answer,
                                    "timestamp": asyncio.get_event_loop().time()
                                }
                            
                            return answer
                        finally:
                            # 强制关闭浏览器，释放资源
                            await browser.close()
            except asyncio.TimeoutError:
                logger.error("AI回答超时")
                return "AI回答超时，请稍后再试"
            except Exception as e:
                logger.error(f"获取AI回答失败: {str(e)}")
                return f"获取AI回答失败，请稍后再试"
    
    def clear_expired_sessions(self):
        """清理过期的会话缓存（超过1小时）"""
        current_time = asyncio.get_event_loop().time()
        expired_users = []
        for user_id, session in self.session_cache.items():
            if current_time - session["timestamp"] > 3600:  # 1小时
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self.session_cache[user_id]

ai_service = AIService()

# 定期清理过期会话
async def cleanup_sessions():
    while True:
        await asyncio.sleep(3600)  # 每小时清理一次
        ai_service.clear_expired_sessions()

# 启动清理任务
import asyncio
loop = asyncio.get_event_loop()
loop.create_task(cleanup_sessions())

