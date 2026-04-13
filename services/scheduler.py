from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from models import db, CrawlerTask, Reminder, PushContent
from services import crawler_service, wechat_service
import asyncio
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.lock_file = "/tmp/auto_assistant_scheduler.lock"
    
    def start(self):
        # 启动前检查是否有其他实例在运行
        if self._acquire_lock():
            try:
                self.scheduler.start()
                # 执行异步的schedule_all_tasks
                import asyncio
                asyncio.create_task(self.schedule_all_tasks())
                logger.info("调度器启动成功")
            except Exception as e:
                logger.error(f"调度器启动失败: {e}")
                self._release_lock()
        else:
            logger.warning("调度器已被其他实例占用，跳过启动")
    
    def stop(self):
        try:
            self.scheduler.shutdown()
            logger.info("调度器停止成功")
        finally:
            self._release_lock()
    
    def _acquire_lock(self):
        """获取单机锁，避免多实例重复执行任务"""
        try:
            # 确保锁文件所在目录存在
            os.makedirs(os.path.dirname(self.lock_file), exist_ok=True)
            
            # 尝试打开锁文件，如果文件已存在且被占用，则获取锁失败
            if os.path.exists(self.lock_file):
                # 检查锁文件是否过期（超过1小时）
                try:
                    import time
                    if time.time() - os.path.getmtime(self.lock_file) > 3600:
                        os.remove(self.lock_file)
                        logger.info("发现过期锁文件，已删除")
                    else:
                        logger.warning("锁文件已存在，可能已有其他实例在运行")
                        return False
                except Exception as e:
                    logger.warning(f"检查锁文件失败: {e}")
                    return False
            
            # 创建锁文件
            self.lock = open(self.lock_file, 'w')
            self.lock.write(f"{os.getpid()}")
            self.lock.flush()
            logger.info("获取锁成功")
            return True
        except Exception as e:
            logger.warning(f"获取锁失败: {e}")
            return False
    
    def _release_lock(self):
        """释放单机锁"""
        try:
            if hasattr(self, 'lock') and self.lock:
                self.lock.close()
                if os.path.exists(self.lock_file):
                    os.remove(self.lock_file)
                logger.info("释放锁成功")
        except Exception as e:
            logger.warning(f"释放锁失败: {e}")
    
    async def schedule_all_tasks(self):
        # 调度爬虫任务
        await self.schedule_crawler_tasks()
        # 调度提醒任务
        await self.schedule_reminder_tasks()
        # 调度推送任务
        await self.schedule_push_tasks()
        # 调度自动更新任务
        self.schedule_update_task()
    
    def _run_async_task(self, async_func, *args, **kwargs):
        """运行异步任务的包装函数"""
        asyncio.create_task(async_func(*args, **kwargs))
    
    async def schedule_crawler_tasks(self):
        try:
            # 使用同步session但在线程池中执行
            def get_tasks():
                return db.session.query(CrawlerTask).filter_by(is_active=True).all()
            
            loop = asyncio.get_event_loop()
            crawler_tasks = await loop.run_in_executor(None, get_tasks)
            for task in crawler_tasks:
                try:
                    self.scheduler.add_job(
                        self._run_async_task,
                        CronTrigger.from_crontab(task.cron_expr),
                        args=[crawler_service.run_crawler, task],
                        id=f"crawler_{task.id}",
                        replace_existing=True
                    )
                    logger.info(f"调度爬虫任务成功: {task.name}")
                except Exception as e:
                    logger.error(f"调度爬虫任务失败: {e}")
        except Exception as e:
            logger.error(f"获取爬虫任务失败: {e}")
    
    async def schedule_reminder_tasks(self):
        """从数据库加载并调度提醒任务"""
        try:
            # 使用同步session但在线程池中执行
            def get_reminders():
                return db.session.query(Reminder).filter_by(is_done=False).all()
            
            loop = asyncio.get_event_loop()
            reminders = await loop.run_in_executor(None, get_reminders)
            
            for reminder in reminders:
                try:
                    # 处理时区，将本地时间（Asia/Shanghai）转换为UTC时间
                    from datetime import timezone
                    try:
                        from pytz import timezone as pytz_timezone
                        # 假设数据库中存储的是上海时区的时间
                        local_tz = pytz_timezone('Asia/Shanghai')
                        # 解析时间字符串并添加时区信息
                        remind_time_local = local_tz.localize(datetime.strptime(reminder.remind_at, "%Y-%m-%d %H:%M:%S"))
                        # 转换为UTC时间
                        remind_time = remind_time_local.astimezone(timezone.utc)
                    except ImportError:
                        # 如果没有安装pytz，使用简单的时区处理
                        remind_time = datetime.strptime(reminder.remind_at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                    
                    now = datetime.now(timezone.utc)
                    if remind_time > now:
                        self.scheduler.add_job(
                            self._run_async_task,
                            "date",
                            run_date=remind_time,
                            args=[self.send_reminder, reminder],
                            id=f"reminder_{reminder.id}",
                            replace_existing=True
                        )
                        logger.info(f"调度提醒任务成功: {reminder.content}")
                except Exception as e:
                    logger.error(f"调度提醒任务失败: {e}")
        except Exception as e:
            logger.error(f"获取提醒任务失败: {e}")
    
    async def schedule_push_tasks(self):
        try:
            # 使用同步session但在线程池中执行
            def get_push_contents():
                return db.session.query(PushContent).filter_by(is_active=True).all()
            
            loop = asyncio.get_event_loop()
            push_contents = await loop.run_in_executor(None, get_push_contents)
            
            for push in push_contents:
                try:
                    # 解析推送时间，格式如 "08:30"
                    hour, minute = map(int, push.push_time.split(":"))
                    self.scheduler.add_job(
                        self._run_async_task,
                        CronTrigger(hour=hour, minute=minute),
                        args=[self.send_push, push],
                        id=f"push_{push.id}",
                        replace_existing=True
                    )
                    logger.info(f"调度推送任务成功: {push.title}")
                except Exception as e:
                    logger.error(f"调度推送任务失败: {e}")
        except Exception as e:
            logger.error(f"获取推送任务失败: {e}")
    
    def schedule_update_task(self):
        """调度自动更新任务"""
        try:
            # 默认每6小时检查一次更新
            update_interval = int(os.getenv("UPDATE_INTERVAL", "6"))
            self.scheduler.add_job(
                self._run_async_task,
                CronTrigger(hour=f"*/{update_interval}"),
                args=[self.check_for_updates],
                id="auto_update",
                replace_existing=True
            )
            logger.info(f"调度自动更新任务成功，每{update_interval}小时检查一次")
        except Exception as e:
            logger.error(f"调度自动更新任务失败: {e}")
    
    async def send_reminder(self, reminder):
        try:
            message = f"提醒: {reminder.content}"
            await wechat_service.send_message(message, to=reminder.user_id)
            reminder.is_done = True
            db.session.commit()
            logger.info(f"发送提醒成功: {reminder.content}")
        except Exception as e:
            logger.error(f"发送提醒失败: {e}")
    
    async def send_push(self, push_content):
        try:
            await wechat_service.send_message(push_content.content, to=push_content.target_group, msgtype="markdown")
            logger.info(f"发送推送成功: {push_content.title}")
        except Exception as e:
            logger.error(f"发送推送失败: {e}")
    
    async def check_for_updates(self):
        """检查自动更新"""
        try:
            from update import check_update
            await check_update()
        except Exception as e:
            logger.error(f"检查更新失败: {e}")

scheduler = Scheduler()

