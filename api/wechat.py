from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import os
from datetime import datetime
from dotenv import load_dotenv
from wechatpy import parse_message, create_reply
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException
from services import wechat_service
from models import db

load_dotenv()

router = APIRouter()


class SendMessageRequest(BaseModel):
    message: str
    to: str = None
    msgtype: str = "text"


@router.get("/webhook")
async def wechat_webhook_verify(request: Request):
    signature = request.query_params.get("signature")
    timestamp = request.query_params.get("timestamp")
    nonce = request.query_params.get("nonce")
    echostr = request.query_params.get("echostr")
    
    token = os.getenv("WECHAT_TOKEN", "your_token")
    
    try:
        check_signature(token, signature, timestamp, nonce)
        return echostr
    except InvalidSignatureException:
        raise HTTPException(status_code=403, detail="Invalid signature")


@router.post("/webhook")
async def wechat_webhook_receive(request: Request):
    body = await request.body()
    try:
        # 解析企业微信消息
        message = parse_message(body)
        
        # 处理不同类型的消息
        if message.type == "text":
            content = message.content
            
            # 处理@助手的情况
            if "@助手" in content:
                # 提取问题
                question = content.replace("@助手", "").strip()
                # 获取AI回答（异步）
                from services import ai_service
                answer = await ai_service.get_ai_answer(question, message.from_user)
                # 回复消息
                reply = create_reply(answer, message)
                return reply.render()
            
            # 处理记忆功能
            elif content.startswith("记住"):
                memory_content = content.replace("记住", "").strip()
                from models import Memory
                new_memory = Memory(
                    user_id=message.from_user,
                    content=memory_content,
                    category="default"
                )
                db.session.add(new_memory)
                db.session.commit()
                reply = create_reply("已记住", message)
                return reply.render()
            
            # 处理提醒功能
            elif content.startswith("提醒我"):
                reminder_content = content.replace("提醒我", "").strip()
                # 这里需要解析时间，简化处理
                from models import Reminder
                new_reminder = Reminder(
                    user_id=message.from_user,
                    content=reminder_content,
                    remind_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                db.session.add(new_reminder)
                db.session.commit()
                reply = create_reply("已设置提醒", message)
                return reply.render()
            
            # 处理理财记录
            elif content.startswith("记录"):
                # 简化处理，实际需要解析金额和类型
                from models import FinanceRecord
                new_record = FinanceRecord(
                    user_id=message.from_user,
                    type="expense",
                    amount=100,
                    category="其他",
                    note=content,
                    record_date=datetime.now().strftime("%Y-%m-%d")
                )
                db.session.add(new_record)
                db.session.commit()
                reply = create_reply("已记录", message)
                return reply.render()
        
        # 默认回复
        reply = create_reply("收到消息", message)
        return reply.render()
    except Exception as e:
        print(f"处理消息失败: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/send")
async def wechat_send_message(request: SendMessageRequest):
    result = wechat_service.send_message(
        message=request.message,
        to=request.to,
        msgtype=request.msgtype
    )
    return result
