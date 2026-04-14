import asyncio
import aiohttp
import logging
import hashlib
from bs4 import BeautifulSoup
from models import db
from services.wechat_service import wechat_service

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CrawlerService:
    def __init__(self):
        self.result_hashes = set()  # 存储已推送的结果哈希
    
    def get_hash(self, content):
        """计算内容的哈希值"""
        return hashlib.md5(content.encode()).hexdigest()
    
    async def run_crawler(self, crawler_task, session=None):
        try:
            logger.info(f"开始执行爬虫任务: {crawler_task.name}")
            
            # 爬取数据
            result = await self.crawl(crawler_task.url, crawler_task.selector)
            
            # 计算结果哈希
            result_hash = self.get_hash(result)
            
            # 检查是否已推送过
            if result_hash in self.result_hashes:
                logger.info(f"爬虫结果未变化，跳过推送: {crawler_task.name}")
                return {"status": "success", "result": result, "message": "结果未变化，跳过推送"}
            
            # 使用传入的session或全局session
            db_session = session or db.session
            
            # 更新爬虫任务结果
            crawler_task.last_result = result
            db_session.commit()
            
            # 发送推送
            await wechat_service.send_message(result, msgtype="markdown")
            
            # 记录已推送的哈希
            self.result_hashes.add(result_hash)
            
            # 限制哈希集合大小，避免内存占用过高
            if len(self.result_hashes) > 1000:
                self.result_hashes = set(list(self.result_hashes)[-500:])
            
            logger.info(f"爬虫任务执行完成: {crawler_task.name}")
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"执行爬虫任务失败: {e}")
            return {"status": "error", "message": str(e)}
    
    async def crawl(self, url, selector):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    response.raise_for_status()
                    html = await response.text()
                    
                    # 解析HTML
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 提取数据
                    if selector:
                        elements = soup.select(selector)
                        result = '\n'.join([elem.get_text(strip=True) for elem in elements])
                    else:
                        result = html
                    
                    return result
        except Exception as e:
            logger.error(f"爬取失败: {e}")
            return f"爬取异常: {str(e)}"

crawler_service = CrawlerService()
