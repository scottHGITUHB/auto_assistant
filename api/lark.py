from fastapi import APIRouter, Request, Response
import logging
import json
from services.lark_bot_service import lark_bot_service

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook/event")
async def handle_webhook(request: Request):
    """处理飞书Webhook事件"""
    try:
        body = await request.body()
        event = json.loads(body.decode('utf-8'))
        
        # 验证令牌
        token = event.get("header", {}).get("token")
        if token != lark_bot_service.verification_token:
            logger.warning(f"无效的验证令牌: {token}")
            return Response(status_code=401, content="Invalid token")
        
        # 处理事件
        result = await lark_bot_service.handle_event(event)
        
        # 返回响应
        return {"code": 0, "data": {}}
    except Exception as e:
        logger.error(f"处理Webhook事件失败: {e}")
        return {"code": 500, "msg": str(e)}

@router.post("/message/send")
async def send_message(request: Request):
    """发送消息"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        text = data.get("text")
        receive_id_type = data.get("receive_id_type", "open_id")
        
        if not user_id or not text:
            return {"code": 400, "msg": "Missing user_id or text"}
        
        result = await lark_bot_service.send_message(user_id, text, receive_id_type)
        return result
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return {"code": 500, "msg": str(e)}

@router.get("/message/list")
async def get_messages(chat_id: str):
    """获取聊天消息列表"""
    try:
        if not chat_id:
            return {"code": 400, "msg": "Missing chat_id"}
        
        result = await lark_bot_service.get_messages(chat_id=chat_id)
        return result
    except Exception as e:
        logger.error(f"获取消息失败: {e}")
        return {"code": 500, "msg": str(e)}

@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "飞书机器人服务"}