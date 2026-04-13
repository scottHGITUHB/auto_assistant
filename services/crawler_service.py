import requests
from bs4 import BeautifulSoup
from models import db

class CrawlerService:
    def run_crawler(self, crawler_task):
        try:
            # 发送HTTP请求
            response = requests.get(crawler_task.url, timeout=30)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取数据
            if crawler_task.selector:
                elements = soup.select(crawler_task.selector)
                result = '\n'.join([elem.get_text(strip=True) for elem in elements])
            else:
                result = response.text
            
            # 更新爬虫任务结果
            crawler_task.last_result = result
            db.session.commit()
            
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

crawler_service = CrawlerService()
