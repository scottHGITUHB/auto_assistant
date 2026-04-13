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
            self.page_pool = []  # 页面池
            self.semaphore = asyncio.Semaphore(3)  # 限制并发数
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
        """获取页面实例，从池中获取或创建新的"""
        async with self.semaphore:
            if not self.browser:
                await self.initialize()
            
            if not self.context:
                self.context = await self.browser.new_context()
            
            # 从池中获取页面
            if self.page_pool:
                return self.page_pool.pop()
            
            # 创建新页面
            page = await self.context.new_page()
            logger.info("创建新页面")
            return page
    
    async def release_page(self, page):
        """释放页面，放回池中"""
        if page:
            self.page_pool.append(page)
            logger.info(f"页面已释放，池中页面数: {len(self.page_pool)}")
    
    async def close(self):
        """关闭浏览器，释放资源"""
        try:
            # 关闭所有页面
            for page in self.page_pool:
                try:
                    await page.close()
                except Exception as e:
                    logger.error(f"关闭页面失败: {e}")
            self.page_pool = []
            
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
