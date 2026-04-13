from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from api import admin, wechat, pushes, crawlers, memories, reminders, finance
from services.scheduler import scheduler
from models import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    db.init_db()
    scheduler.start()
    yield
    # 关闭时执行
    scheduler.stop()


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


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
