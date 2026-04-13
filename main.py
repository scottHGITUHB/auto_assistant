from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
import os
from dotenv import load_dotenv

from api import admin, wechat, pushes, crawlers, memories, reminders, finance
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
        
        # 启动时检查更新
        try:
            from update import check_update_on_start
            await check_update_on_start()
        except Exception as e:
            logger.warning(f"启动时检查更新失败: {e}")
        
        yield
        
        # 关闭时执行
        logger.info("正在停止调度器...")
        scheduler.stop()
        logger.info("调度器停止完成")
    except Exception as e:
        logger.error(f"服务生命周期管理失败: {e}")
        raise


app = FastAPI(
    title="企业微信机器人API",
    description="企业微信机器人应用，集成自动化问答、信息推送、数据爬取和个人助理功能",
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

# 注册路由
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(wechat.router, prefix="/api/wechat", tags=["wechat"])
app.include_router(pushes.router, prefix="/api/pushes", tags=["pushes"])
app.include_router(crawlers.router, prefix="/api/crawlers", tags=["crawlers"])
app.include_router(memories.router, prefix="/api/memories", tags=["memories"])
app.include_router(reminders.router, prefix="/api/reminders", tags=["reminders"])
app.include_router(finance.router, prefix="/api/finance", tags=["finance"])


@app.get("/")
async def root():
    return {"message": "企业微信机器人API服务运行中"}


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "企业微信机器人API"}


@app.get("/api/dashboard/stats")
async def dashboard_stats():
    """仪表盘统计数据"""
    from datetime import datetime
    from models import db, PushContent, MessageLog
    
    try:
        # 统计今日推送数
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 这里可以添加具体的统计逻辑
        # 例如：统计今日推送数量、消息处理数量等
        
        return {
            "today_pushes": 0,
            "message_stats": 0,
            "task_status": "正常"
        }
    except Exception as e:
        logger.error(f"获取仪表盘统计数据失败: {e}")
        return {
            "today_pushes": 0,
            "message_stats": 0,
            "task_status": "正常"
        }


if __name__ == "__main__":
    try:
        logger.info("正在启动企业微信机器人API服务...")
        uvicorn.run(
            "main:app", 
            host="0.0.0.0", 
            port=8000, 
            reload=False,
            log_config=None  # 使用自定义日志配置
        )
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        raise

