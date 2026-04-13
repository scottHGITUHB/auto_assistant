import asyncio
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QueueService:
    """队列服务，处理后台任务"""
    def __init__(self):
        self.task_queue = asyncio.Queue()
        self.processed_ids = set()  # 消息去重
        self.last_call = {}  # 限流
        self.worker_running = False
    
    async def start_worker(self):
        """启动工作线程"""
        if not self.worker_running:
            self.worker_running = True
            asyncio.create_task(self.worker())
            logger.info("队列工作线程已启动")
    
    async def worker(self):
        """工作线程，处理队列中的任务"""
        while True:
            try:
                task = await self.task_queue.get()
                await self.handle_task(task)
            except Exception as e:
                logger.error(f"处理任务失败: {e}")
            finally:
                self.task_queue.task_done()
    
    async def handle_task(self, task):
        """处理具体任务"""
        task_type = task.get("type")
        
        if task_type == "ai_request":
            await self.handle_ai_request(task)
        elif task_type == "wechat_message":
            await self.handle_wechat_message(task)
        else:
            logger.warning(f"未知任务类型: {task_type}")
    
    async def handle_ai_request(self, task):
        """处理AI请求"""
        question = task.get("question")
        user_id = task.get("user_id")
        message = task.get("message")
        
        try:
            from .ai_service import ai_service
            from .wechat_service import wechat_service
            
            # 获取AI回答
            answer = await ai_service.get_ai_answer(question, user_id)
            
            # 发送回答
            await wechat_service.send_message(answer, to=user_id)
            
            logger.info(f"AI请求处理完成: {question[:50]}...")
        except Exception as e:
            logger.error(f"处理AI请求失败: {e}")
    
    async def handle_wechat_message(self, task):
        """处理微信消息"""
        # 这里可以添加其他微信消息的处理逻辑
        pass
    
    async def add_task(self, task):
        """添加任务到队列"""
        # 消息去重
        message_id = task.get("message_id")
        if message_id and message_id in self.processed_ids:
            logger.info(f"消息已处理，跳过: {message_id}")
            return False
        
        if message_id:
            self.processed_ids.add(message_id)
            # 定期清理过期的消息ID（保留24小时）
            self._cleanup_processed_ids()
        
        # 限流
        user_id = task.get("user_id")
        if user_id and not self._rate_limit(user_id):
            logger.warning(f"用户请求过于频繁，限流: {user_id}")
            return False
        
        await self.task_queue.put(task)
        logger.info(f"任务已添加到队列: {task.get('type')}")
        return True
    
    def _rate_limit(self, user, interval=5):
        """限流检查"""
        import time
        now = time.time()
        if user in self.last_call and now - self.last_call[user] < interval:
            return False
        self.last_call[user] = now
        return True
    
    def _cleanup_processed_ids(self):
        """清理过期的处理消息ID"""
        # 这里可以添加清理逻辑，例如保留最近24小时的消息ID
        pass

# 创建全局实例
queue_service = QueueService()
