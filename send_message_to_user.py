#!/usr/bin/env python3
"""
发送消息给用户
"""

import asyncio
import logging
from services.lark_bot_service import lark_bot_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def send_message_to_user():
    """发送消息给用户"""
    logger.info("=== 发送消息给用户 ===")
    
    # 启动机器人
    start_result = await lark_bot_service.start()
    if not start_result:
        logger.error("飞书机器人启动失败")
        return
    
    # 发送包含用户名字的消息
    user_id = "ou_1234567890"  # 替换为实际的用户ID
    message = f"你好，轻风！这是一条来自自动小助手的消息。"
    
    send_result = await lark_bot_service.send_message(user_id, message)
    if send_result.get("errcode") == 0:
        logger.info("✅ 消息发送成功")
        logger.info(f"发送的消息: {message}")
    else:
        logger.error(f"❌ 消息发送失败: {send_result}")
    
    logger.info("=== 发送完成 ===")

if __name__ == "__main__":
    try:
        asyncio.run(send_message_to_user())
    except Exception as e:
        logger.error(f"发送消息时发生错误: {e}")