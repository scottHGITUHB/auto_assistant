from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from models import db, CrawlerTask, Reminder, PushContent
from services import crawler_service, wechat_service
import asyncio
import logging
import os
import fcntl

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
                self.schedule_all_tasks()
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
            
            self.lock = open(self.lock_file, 'w')
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock.write(f"{os.getpid()}")
            self.lock.flush()
            return True
        except Exception as e:
            logger.warning(f"获取锁失败，可能已有其他实例在运行: {e}")
            return False
    
    def _release_lock(self):
        """释放单机锁"""
        try:
            if hasattr(self, 'lock') and self.lock:
                fcntl.flock(self.lock, fcntl.LOCK_UN)
                self.lock.close()
                os.remove(self.lock_file)
        except Exception as e:
            logger.warning(f"释放锁失败: {e}")
    
    def schedule_all_tasks(self):
        # 调度爬虫任务
        self.schedule_crawler_tasks()
        # 调度提醒任务
        self.schedule_reminder_tasks()
        # 调度推送任务
        self.schedule_push_tasks()
        # 调度自动更新任务
        self.schedule_update_task()
    
    def schedule_crawler_tasks(self):
        try:
            crawler_tasks = db.session.query(CrawlerTask).filter_by(is_active=True).all()
            for task in crawler_tasks:
                try:
                    self.scheduler.add_job(
                        crawler_service.run_crawler,
                        CronTrigger.from_crontab(task.cron_expr),
                        args=[task],
                        id=f"crawler_{task.id}",
                        replace_existing=True
                    )
                    logger.info(f"调度爬虫任务成功: {task.name}")
                except Exception as e:
                    logger.error(f"调度爬虫任务失败: {e}")
        except Exception as e:
            logger.error(f"获取爬虫任务失败: {e}")
    
    def schedule_reminder_tasks(self):
        try:
            reminders = db.session.query(Reminder).filter_by(is_done=False).all()
            for reminder in reminders:
                try:
                    remind_time = datetime.strptime(reminder.remind_at, "%Y-%m-%d %H:%M:%S")
                    if remind_time > datetime.now():
                        self.scheduler.add_job(
                            self.send_reminder,
                            "date",
                            run_date=remind_time,
                            args=[reminder],
                            id=f"reminder_{reminder.id}",
                            replace_existing=True
                        )
                        logger.info(f"调度提醒任务成功: {reminder.content}")
                except Exception as e:
                    logger.error(f"调度提醒任务失败: {e}")
        except Exception as e:
            logger.error(f"获取提醒任务失败: {e}")
    
    def schedule_push_tasks(self):
        try:
            push_contents = db.session.query(PushContent).filter_by(is_active=True).all()
            for push in push_contents:
                try:
                    # 解析推送时间，格式如 "08:30"
                    hour, minute = map(int, push.push_time.split(":"))
                    self.scheduler.add_job(
                        self.send_push,
                        CronTrigger(hour=hour, minute=minute),
                        args=[push],
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
                self.check_for_updates,
                CronTrigger(hour=f"*/{update_interval}"),
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

