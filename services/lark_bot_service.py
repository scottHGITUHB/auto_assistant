import os
import asyncio
import logging
import json
from dotenv import load_dotenv
from lark_oapi.client import Client, Config
from lark_oapi.api.im.v1 import *

load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LarkBotService:
    def __init__(self):
        self.app_id = os.getenv("LARK_APP_ID")
        self.app_secret = os.getenv("LARK_APP_SECRET")
        self.encrypt_key = os.getenv("LARK_ENCRYPT_KEY", "Mb4uBc6RT3xpEYFVg5q3Hb4Z3WDYQGyf")
        self.verification_token = os.getenv("LARK_VERIFICATION_TOKEN", "JrWhu02UXj477mfa6fhbnb8duwXagOX5")
        self.lark = None
        self.is_connected = False
        
    async def start(self):
        """启动飞书机器人"""
        try:
            if not self.app_id or not self.app_secret:
                logger.error("飞书机器人启动失败: 缺少App ID或App Secret")
                return False
            
            # 初始化飞书SDK
            self.lark = Client.builder()\
                .app_id(self.app_id)\
                .app_secret(self.app_secret)\
                .build()
            self.is_connected = True
            logger.info("飞书机器人启动成功")
            return True
        except Exception as e:
            logger.error(f"飞书机器人启动失败: {e}")
            return False
    
    async def send_message(self, user_id, text, receive_id_type="open_id"):
        """发送消息（私聊或群聊）"""
        try:
            if not self.lark or not self.is_connected:
                logger.error("飞书机器人未连接")
                return {"errcode": 401, "errmsg": "飞书机器人未连接"}
            
            logger.info(f"发送消息到: {user_id}, 类型: {receive_id_type}")
            logger.info(f"消息内容: {text}")
            
            # 构造消息请求
            request = CreateMessageRequest.builder()\
                .receive_id_type(receive_id_type)\
                .request_body(CreateMessageRequestBody.builder()\
                    .receive_id(user_id)\
                    .content(json.dumps({"text": text}))\
                    .msg_type("text")\
                    .build())\
                .build()
            
            # 发送消息
            response = self.lark.im.v1.message.create(request)
            
            # 处理响应
            if response.code == 0:
                logger.info("✅ 消息发送成功")
                return {"errcode": 0, "errmsg": "ok"}
            else:
                logger.error(f"❌ 消息发送失败: {response.msg}")
                return {"errcode": response.code, "errmsg": response.msg}
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return {"errcode": 500, "errmsg": str(e)}
    
    async def get_messages(self, container_id_type="chat", container_id=None, chat_id=None):
        """获取聊天消息记录"""
        try:
            if not self.lark or not self.is_connected:
                logger.error("飞书机器人未连接")
                return {"errcode": 401, "errmsg": "飞书机器人未连接"}
            
            # 如果提供了chat_id，使用它
            target_id = chat_id if chat_id else container_id
            if not target_id:
                logger.error("缺少 chat_id 或 container_id")
                return {"errcode": 400, "errmsg": "缺少 chat_id 或 container_id"}
            
            logger.info(f"获取消息记录: chat_id={target_id}")
            
            # 使用API获取消息列表
            request = ListMessageRequest.builder()\
                .container_id_type(container_id_type)\
                .container_id(target_id)\
                .page_size(10)\
                .build()
            
            # 发送请求
            response = self.lark.im.v1.message.list(request)
            
            # 处理响应
            if response.code == 0:
                logger.info("✅ 获取消息成功")
                messages = []
                if response.data and response.data.items:
                    for msg in response.data.items:
                        try:
                            body_content = msg.body.content if hasattr(msg.body, "content") else ""
                            sender_id = msg.sender.id if hasattr(msg.sender, "id") else ""
                            
                            text_content = ""
                            if body_content:
                                try:
                                    content_json = json.loads(body_content)
                                    text_content = content_json.get("text", "")
                                except:
                                    text_content = body_content
                            
                            messages.append({
                                "message_id": msg.message_id,
                                "sender": sender_id,
                                "content": text_content,
                                "create_time": msg.create_time
                            })
                        except Exception as msg_error:
                            logger.warning(f"解析消息失败: {msg_error}")
                            messages.append({
                                "message_id": getattr(msg, "message_id", ""),
                                "sender": "",
                                "content": "",
                                "create_time": getattr(msg, "create_time", "")
                            })
                return {"errcode": 0, "errmsg": "ok", "data": {"messages": messages}}
            else:
                logger.error(f"❌ 获取消息失败: {response.msg}")
                return {"errcode": response.code, "errmsg": response.msg}
        except Exception as e:
            logger.error(f"获取消息失败: {e}")
            return {"errcode": 500, "errmsg": str(e)}
    
    async def handle_event(self, event):
        """处理飞书事件"""
        try:
            event_type = event.get("header", {}).get("event_type")
            if event_type == "im.message.receive_v1":
                message = event.get("event", {})
                user_id = message.get("sender", {}).get("sender_id", {}).get("open_id")
                content = json.loads(message.get("message", {}).get("content", "{}")).get("text")
                
                logger.info(f"收到消息: {content} 来自: {user_id}")
                
                # 处理命令
                if content.startswith('/'):
                    return await self.handle_command(content, user_id)
                else:
                    # 直接调用AI
                    return await self.handle_ai_query(content, user_id)
            
            return {"code": 0, "data": {}}
        except Exception as e:
            logger.error(f"处理事件失败: {e}")
            return {"code": 500, "msg": str(e)}
    
    async def handle_command(self, content, user_id):
        """处理命令"""
        if content == "/菜单":
            menu_text = "我是自动小助手，您可以使用以下命令：\n\n"
            menu_text += "/菜单 - 查看可用命令\n"
            menu_text += "/记住事项 + 内容 - 存储事项\n"
            menu_text += "/记账 + 内容 - 记录财务\n"
            menu_text += "/时间提醒 + 内容 - 设置提醒\n"
            menu_text += "/搜索 + 内容 - 搜索信息\n"
            menu_text += "\n直接输入问题 - 获取AI助手回答"
            await self.send_message(user_id, menu_text)
        
        # 其他命令处理...
        
        return {"code": 0, "data": {}}
    
    async def handle_ai_query(self, question, user_id):
        """处理AI查询"""
        # 从队列服务添加任务
        try:
            from .queue_service import queue_service
            await queue_service.add_task({
                "type": "ai_request",
                "question": question,
                "user_id": user_id
            })
            await self.send_message(user_id, "收到您的问题，正在处理中...")
        except Exception as e:
            logger.error(f"处理AI查询失败: {e}")
            await self.send_message(user_id, "处理您的问题时发生错误，请稍后重试")
        
        return {"code": 0, "data": {}}

# 创建全局实例
lark_bot_service = LarkBotService()

async def start_bot():
    """启动飞书机器人"""
    return await lark_bot_service.start()