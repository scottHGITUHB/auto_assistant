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
        self.ai_web_url = os.getenv("AI_WEB_URL", "https://kimi.moonshot.cn/chat")
        self.ai_username = os.getenv("AI_USERNAME")
        self.ai_password = os.getenv("AI_PASSWORD")
        self.ai_timeout = int(os.getenv("AI_TIMEOUT", "30000"))  # 改为30秒超时
        self.session_cache = {}  # 内存级会话缓存
        self.semaphore = asyncio.Semaphore(5)  # 并发限制，最多5个并行请求
    
    async def extract_answer(self, page):
        """使用多策略提取AI回答"""
        selectors = [
            ".chat-content",
            ".kimi-message",
            ".markdown",
            ".message",
            "[data-message-author-role='assistant']",
            ".chat-message-content",
            ".response",
            ".ai-answer",
            ".answer-content"
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
            logger.info(f"访问AI网站: {self.ai_web_url}")
            # 访问AI网站
            await page.goto(self.ai_web_url, timeout=self.ai_timeout)
            
            # 等待页面加载完成
            logger.info("等待页面加载完成...")
            await page.wait_for_load_state("networkidle", timeout=self.ai_timeout)
            
            # 打印页面标题
            title = await page.title()
            logger.info(f"页面标题: {title}")
            
            # 检查是否需要登录
            logger.info("检查是否需要登录...")
            try:
                # 首先尝试点击左下角用户头像（根据Kimi AI的界面）
                logger.info("尝试点击左下角用户头像...")
                user_avatar_selectors = [
                    ".user-avatar",  # 用户头像
                    "[class*='avatar']",  # 包含avatar的类
                    "img[alt*='user']",  # 用户图片
                    "#user-avatar",  # 用户头像ID
                    ".avatar"  # 头像类
                ]
                
                clicked_avatar = False
                for selector in user_avatar_selectors:
                    try:
                        avatar_element = await page.query_selector(selector)
                        if avatar_element:
                            logger.info(f"找到用户头像: {selector}")
                            # 检查元素是否可见
                            is_visible = await avatar_element.is_visible()
                            logger.info(f"用户头像是否可见: {is_visible}")
                            if is_visible:
                                await avatar_element.click()
                                logger.info("已点击用户头像")
                                clicked_avatar = True
                                break
                            else:
                                logger.warning("用户头像不可见")
                    except Exception as e:
                        logger.warning(f"点击用户头像 {selector} 失败: {e}")
                
                # 如果没有找到用户头像，尝试截取页面截图
                if not clicked_avatar:
                    logger.warning("未找到用户头像，截取页面截图...")
                    screenshot_path = "page_screenshot.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    logger.info(f"页面截图已保存到 {screenshot_path}")
                    
                    # 保存页面内容到文件，以便分析
                    content = await page.content()
                    with open("page_content.html", "w", encoding="utf-8") as f:
                        f.write(content)
                    logger.info("页面内容已保存到page_content.html")
                
                # 等待登录界面出现
                if clicked_avatar:
                    logger.info("等待登录界面出现...")
                    await asyncio.sleep(2)  # 等待2秒
                
                # 检查是否存在登录二维码
                qr_code_selector = "img[src*='qrcode']"  # 二维码图片
                login_form_selector = "form"  # 登录表单
                
                # 检查是否存在登录相关元素
                has_qr_code = await page.query_selector(qr_code_selector) is not None
                has_login_form = await page.query_selector(login_form_selector) is not None
                
                if has_qr_code or has_login_form:
                    logger.info("检测到登录页面，需要登录")
                    
                    # 截取登录页面截图
                    login_screenshot_path = "kimi_login_qr.png"
                    await page.screenshot(path=login_screenshot_path, full_page=True)
                    logger.info(f"登录二维码已保存到 {login_screenshot_path}")
                    
                    # 等待用户扫码登录
                    logger.info("请扫描登录二维码进行登录...")
                    logger.info("登录成功后，脚本将继续执行")
                    
                    # 等待输入框出现（表示登录成功）
                    await page.wait_for_selector("[contenteditable='true']", timeout=300000)  # 5分钟超时，给用户足够时间扫码
                    logger.info("登录成功，输入框已出现")
                else:
                    logger.info("无需登录或已经登录")
            except Exception as e:
                logger.warning(f"登录检测失败: {e}")
            
            # 等待输入框出现（优先查找contenteditable，适配Kimi AI）
            logger.info("等待输入框出现...")
            try:
                # 尝试等待contenteditable输入框出现（Kimi AI使用）
                await page.wait_for_selector("[contenteditable='true']", timeout=10000)
                logger.info("contenteditable输入框已出现")
            except Exception as e:
                logger.warning(f"等待contenteditable输入框失败: {e}")
                try:
                    # 回退：等待textarea输入框出现
                    await page.wait_for_selector("textarea", timeout=10000)
                    logger.info("textarea输入框已出现")
                except Exception as e2:
                    logger.warning(f"等待textarea输入框也失败: {e2}")
            
            # 尝试找到输入框（适配Kimi AI）
            input_selectors = [
                "[contenteditable='true']",  # 优先查找contenteditable（Kimi AI使用）
                "textarea",
                "input[type='text']"
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    input_element = await page.query_selector(selector)
                    if input_element:
                        logger.info(f"找到输入框: {selector}")
                        # 检查输入框是否可见
                        is_visible = await input_element.is_visible()
                        logger.info(f"输入框是否可见: {is_visible}")
                        break
                except Exception as e:
                    logger.warning(f"查找输入框 {selector} 失败: {e}")
            
            if not input_element:
                # 尝试获取页面内容，看看页面结构
                content = await page.content()
                logger.info(f"页面内容长度: {len(content)}")
                # 保存页面内容到文件，以便分析
                with open("page_content.html", "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info("页面内容已保存到page_content.html")
                # 截取页面截图
                screenshot_path = "page_screenshot.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"页面截图已保存到 {screenshot_path}")
                raise Exception("无法找到输入框")
            
            # 输入问题
            logger.info(f"输入问题: {question}")
            # 对于contenteditable元素，使用type而不是fill
            if "contenteditable" in input_element._selector:
                await input_element.type(question)
            else:
                await input_element.fill(question)
            
            # 直接按Enter键发送（根据Kimi AI的操作流程）
            logger.info("按Enter键发送问题...")
            await input_element.press("Enter")
            logger.info("问题已发送")
            
            # 等待回答生成
            logger.info("等待回答生成...")
            # 等待更长时间，确保回答完全生成
            await asyncio.sleep(10)  # 等待10秒
            
            # 尝试提取回答
            logger.info("尝试提取回答...")
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
