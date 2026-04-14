import os
import asyncio
from dotenv import load_dotenv
import logging
from .browser_manager import browser_manager

# 兼容Python 3.10及以下版本的asyncio.timeout
try:
    from asyncio import timeout as asyncio_timeout
except ImportError:
    # Python 3.10及以下使用wait_for包装
    import asyncio
    from contextlib import asynccontextmanager
    
    @asynccontextmanager
    async def asyncio_timeout(timeout):
        try:
            yield
        except asyncio.TimeoutError:
            raise

load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.ai_web_url = os.getenv("AI_WEB_URL", "https://chat.openai.com")
        self.ai_username = os.getenv("AI_USERNAME")
        self.ai_password = os.getenv("AI_PASSWORD")
        self.ai_timeout = int(os.getenv("AI_TIMEOUT", "30000"))  # 改为30秒超时
        self.session_cache = {}  # 内存级会话缓存
        self.semaphore = asyncio.Semaphore(5)  # 并发限制，最多5个并行请求
    
    async def extract_answer(self, page):
        """使用多策略提取AI回答"""
        selectors = [
            ".markdown",
            ".message",
            "[data-message-author-role='assistant']",
            ".chat-message-content",
            ".response"
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    answer = await element.inner_text()
                    if answer.strip():
                        return answer
            except Exception as e:
                logger.warning(f"使用选择器 {selector} 提取回答失败: {e}")
        
        raise Exception("所有选择器都提取失败")
    
    async def run_ai(self, question, user_id=None):
        """运行AI请求"""
        page = await browser_manager.get_page()
        answer = None
        
        try:
            # 访问AI网站
            await page.goto(self.ai_web_url, timeout=self.ai_timeout)
            
            # 登录流程
            if self.ai_username and self.ai_password:
                try:
                    # 点击登录按钮
                    await page.click("button:has-text('Log in')", timeout=10000)
                    
                    # 输入用户名
                    await page.fill("input[type='email']", self.ai_username)
                    await page.click("button:has-text('Continue')", timeout=10000)
                    
                    # 输入密码
                    await page.fill("input[type='password']", self.ai_password)
                    await page.click("button:has-text('Log in')", timeout=10000)
                    
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
            await asyncio.sleep(2)  # 等待输入完成
            
            # 尝试提取回答
            answer = await self.extract_answer(page)
            
            # 更新会话缓存
            if user_id:
                self.session_cache[user_id] = {
                    "question": question,
                    "answer": answer,
                    "timestamp": asyncio.get_event_loop().time()
                }
            
            return answer
        except Exception as e:
            logger.error(f"AI处理失败: {e}")
            raise
        finally:
            # 成功才回收页面，失败则关闭页面
            if answer:
                await browser_manager.release_page(page)
            else:
                try:
                    await page.close()
                    logger.info("页面处理失败，已关闭页面")
                except Exception as close_error:
                    logger.warning(f"关闭页面失败: {close_error}")
    
    async def get_ai_answer(self, question, user_id=None):
        """获取AI回答，支持超时和重试"""
        # 使用并发锁限制并行请求
        async with self.semaphore:
            max_retries = 2
            retry_count = 0
            
            while retry_count <= max_retries:
                try:
                    # 超时控制
                    try:
                        from asyncio import timeout as asyncio_timeout
                        # Python 3.11+ 使用内置timeout
                        async with asyncio_timeout(self.ai_timeout / 1000):
                            answer = await self.run_ai(question, user_id)
                    except ImportError:
                        # Python 3.10及以下使用wait_for
                        answer = await asyncio.wait_for(self.run_ai(question, user_id), timeout=self.ai_timeout / 1000)
                    
                    logger.info(f"AI回答成功，长度: {len(answer)}")
                    return answer
                except asyncio.TimeoutError:
                    retry_count += 1
                    if retry_count > max_retries:
                        logger.error("AI回答超时，已达到最大重试次数")
                        return "AI回答超时，请稍后重试"
                    logger.warning(f"AI回答超时，正在重试 ({retry_count}/{max_retries})...")
                    await asyncio.sleep(2)  # 等待2秒后重试
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

# 启动清理任务的函数，供main.py调用
async def start_cleanup_task():
    asyncio.create_task(cleanup_sessions())
