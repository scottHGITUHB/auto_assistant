from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models.db import SessionLocal, SystemLog, MessageLog
from datetime import datetime
from typing import List, Optional

router = APIRouter()


class SystemLogResponse(BaseModel):
    id: int
    level: str
    module: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageLogResponse(BaseModel):
    id: int
    direction: str
    content: str
    response: Optional[str]
    status: str
    error_msg: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CreateSystemLogRequest(BaseModel):
    level: str
    module: str
    message: str


@router.get("/system", response_model=List[SystemLogResponse])
async def get_system_logs(limit: int = 100, level: Optional[str] = None):
    """获取系统日志"""
    session = SessionLocal()
    try:
        query = session.query(SystemLog).order_by(SystemLog.created_at.desc())
        
        if level:
            query = query.filter(SystemLog.level == level)
        
        logs = query.limit(limit).all()
        return logs
    finally:
        session.close()


@router.post("/system", response_model=SystemLogResponse)
async def create_system_log(request: CreateSystemLogRequest):
    """创建系统日志"""
    session = SessionLocal()
    try:
        log = SystemLog(
            level=request.level,
            module=request.module,
            message=request.message
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log
    finally:
        session.close()


@router.delete("/system/{log_id}")
async def delete_system_log(log_id: int):
    """删除系统日志"""
    session = SessionLocal()
    try:
        log = session.query(SystemLog).filter(SystemLog.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="日志不存在")
        
        session.delete(log)
        session.commit()
        return {"message": "删除成功"}
    finally:
        session.close()


@router.get("/messages", response_model=List[MessageLogResponse])
async def get_message_logs(limit: int = 100, direction: Optional[str] = None):
    """获取消息日志"""
    session = SessionLocal()
    try:
        query = session.query(MessageLog).order_by(MessageLog.created_at.desc())
        
        if direction:
            query = query.filter(MessageLog.direction == direction)
        
        logs = query.limit(limit).all()
        return logs
    finally:
        session.close()


@router.delete("/messages/{log_id}")
async def delete_message_log(log_id: int):
    """删除消息日志"""
    session = SessionLocal()
    try:
        log = session.query(MessageLog).filter(MessageLog.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="日志不存在")
        
        session.delete(log)
        session.commit()
        return {"message": "删除成功"}
    finally:
        session.close()
