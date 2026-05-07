from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import logging
import os
from dotenv import load_dotenv

from api import admin, pushes, crawlers, memories, reminders, finance, logs, chat
from services.scheduler import scheduler
from models import db

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    try:
        logger.info("正在初始化数据库...")
        db.init_db()
        logger.info("数据库初始化完成")

        logger.info("正在启动调度器...")
        scheduler.start()
        logger.info("调度器启动完成")

        logger.info("正在启动队列服务...")
        from services.queue_service import queue_service
        await queue_service.start_worker()
        logger.info("队列服务启动完成")

        # 启动AI服务的清理任务
        try:
            from services.ai_service import start_cleanup_task
            await start_cleanup_task()
            logger.info("AI服务清理任务启动完成")
        except Exception as e:
            logger.warning(f"启动AI服务清理任务失败: {e}")

        yield

        # 关闭时执行
        logger.info("正在停止调度器...")
        scheduler.stop()
        logger.info("调度器停止完成")
    except Exception as e:
        logger.error(f"服务生命周期管理失败: {e}")
        raise


app = FastAPI(
    title="自动小助手API",
    description="智能机器人应用，集成自动化问答、信息推送、数据爬取和个人助理功能",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常捕获
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全局异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "服务器内部错误", "message": str(exc)}
    )

# 注册API路由
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(pushes.router, prefix="/api/pushes", tags=["pushes"])
app.include_router(crawlers.router, prefix="/api/crawlers", tags=["crawlers"])
app.include_router(memories.router, prefix="/api/memories", tags=["memories"])
app.include_router(reminders.router, prefix="/api/reminders", tags=["reminders"])
app.include_router(finance.router, prefix="/api/finance", tags=["finance"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

# 注册其他路由
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "企业微信机器人API"}


@app.get("/api/dashboard/stats")
async def dashboard_stats():
    """仪表盘统计数据"""
    from datetime import datetime
    from models.db import SessionLocal, PushContent, MessageLog

    session = SessionLocal()
    try:
        today = datetime.now().strftime("%Y-%m-%d")

        # 统计今日推送数
        today_pushes = session.query(PushContent).filter(
            PushContent.created_at >= today
        ).count()

        # 统计今日消息数
        message_stats = session.query(MessageLog).filter(
            MessageLog.created_at >= today
        ).count()

        return {
            "today_pushes": today_pushes,
            "message_stats": message_stats,
            "task_status": "正常"
        }
    except Exception as e:
        logger.error(f"获取仪表盘统计数据失败: {e}")
        return {
            "today_pushes": 0,
            "message_stats": 0,
            "task_status": "正常"
        }
    finally:
        session.close()

# 挂载静态文件目录（最后挂载，确保API路由优先）
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")


if __name__ == "__main__":
    import time
    max_retries = 0  # 0表示无限重试
    retry_count = 0
    retry_delay = 5  # 重启延迟（秒）

    logger.info("自动小助手服务启动中...")

    while True:
        try:
            logger.info(f"正在启动服务... (重试次数: {retry_count})")
            uvicorn.run(
                "main:app",
                host="0.0.0.0",
                port=8080,
                reload=False,
                log_config=None
            )
        except KeyboardInterrupt:
            logger.info("收到停止信号，服务正在关闭...")
            break
        except Exception as e:
            retry_count += 1
            logger.error(f"服务异常退出: {e}")
            if max_retries > 0 and retry_count >= max_retries:
                logger.error(f"已达到最大重试次数 ({max_retries})，退出程序")
                break
            logger.info(f"{retry_delay}秒后自动重启...")
            time.sleep(retry_delay)