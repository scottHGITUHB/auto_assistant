import asyncio
from playwright.async_api import async_playwright
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BrowserManager:
    """浏览器管理类，实现浏览器复用"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.browser = None
            self.context = None
            self.page = None
            self._initialized = True
    
    async def initialize(self):
        """初始化浏览器"""
        if not self.browser:
            try:
                logger.info("正在启动浏览器...")
                playwright = await async_playwright().start()
                self.browser = await playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-extensions"
                    ]
                )
                logger.info("浏览器启动成功")
            except Exception as e:
                logger.error(f"浏览器启动失败: {e}")
                raise
    
    async def get_page(self):
        """获取页面实例，按需创建"""
        if not self.browser:
            await self.initialize()
        
        if not self.context:
            self.context = await self.browser.new_context()
        
        if not self.page:
            self.page = await self.context.new_page()
        
        return self.page
    
    async def close(self):
        """关闭浏览器，释放资源"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")

# 创建全局实例
browser_manager = BrowserManager()
