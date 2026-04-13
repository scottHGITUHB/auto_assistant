from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from models import db, CrawlerTask, Reminder, PushContent
from services import crawler_service, wechat_service

class Scheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
    
    def start(self):
        self.scheduler.start()
        self.schedule_all_tasks()
    
    def stop(self):
        self.scheduler.shutdown()
    
    def schedule_all_tasks(self):
        # 调度爬虫任务
        self.schedule_crawler_tasks()
        # 调度提醒任务
        self.schedule_reminder_tasks()
        # 调度推送任务
        self.schedule_push_tasks()
    
    def schedule_crawler_tasks(self):
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
            except Exception as e:
                print(f"调度爬虫任务失败: {e}")
    
    def schedule_reminder_tasks(self):
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
            except Exception as e:
                print(f"调度提醒任务失败: {e}")
    
    def schedule_push_tasks(self):
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
            except Exception as e:
                print(f"调度推送任务失败: {e}")
    
    def send_reminder(self, reminder):
        try:
            message = f"提醒: {reminder.content}"
            wechat_service.send_message(message, to=reminder.user_id)
            reminder.is_done = True
            db.session.commit()
        except Exception as e:
            print(f"发送提醒失败: {e}")
    
    def send_push(self, push_content):
        try:
            wechat_service.send_message(push_content.content, to=push_content.target_group, msgtype="markdown")
        except Exception as e:
            print(f"发送推送失败: {e}")

scheduler = Scheduler()
