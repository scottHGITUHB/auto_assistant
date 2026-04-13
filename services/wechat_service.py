import os
import asyncio
import aiohttp
import json
from dotenv import load_dotenv
import logging

load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WeChatService:
    def __init__(self):
        self.corpid = os.getenv("WECHAT_CORPID")
        self.secret = os.getenv("WECHAT_SECRET")
        self.agentid = os.getenv("WECHAT_AGENTID")
        self.webhook_key = os.getenv("WECHAT_WEBHOOK_KEY")
        self.access_token = None
        self.expire_time = 0  # token过期时间
        self.session = None
    
    async def get_session(self):
        """获取aiohttp会话"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close_session(self):
        """关闭aiohttp会话"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_access_token(self):
        """异步获取access token，带缓存"""
        import time
        now = time.time()
        
        # 检查token是否有效（提前300秒刷新）
        if self.access_token and now < self.expire_time - 300:
            return self.access_token
        
        # 需要重新获取token
        session = await self.get_session()
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corpid}&corpsecret={self.secret}"
        try:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("errcode") == 0:
                        self.access_token = result.get("access_token")
                        # 设置过期时间（企业微信token有效期为7200秒）
                        self.expire_time = now + result.get("expires_in", 7200)
                        logger.info("获取access token成功，有效期7200秒")
        except Exception as e:
            logger.error(f"获取access token失败: {e}")
        return self.access_token
    
    def escape_special_chars(self, message):
        """处理特殊字符，避免企微接口报错"""
        # 处理企微接口不支持的特殊字符
        special_chars = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            "\"": "&quot;",
            "'": "&#39;"
        }
        for char, replacement in special_chars.items():
            message = message.replace(char, replacement)
        return message
    
    async def send_message(self, message, to=None, msgtype="text"):
        """异步发送消息，支持重试机制"""
        max_retries = 3
        retry_delay = 2  # 秒
        
        # 处理特殊字符
        message = self.escape_special_chars(message)
        
        for retry in range(max_retries):
            try:
                session = await self.get_session()
                
                if self.webhook_key:
                    # 使用webhook发送消息
                    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self.webhook_key}"
                    data = {
                        "msgtype": msgtype
                    }
                    if msgtype == "text":
                        data["text"] = {"content": message}
                    elif msgtype == "markdown":
                        data["markdown"] = {"content": message}
                else:
                    # 使用企业微信应用发送消息
                    access_token = await self.get_access_token()
                    if not access_token:
                        raise Exception("获取access token失败")
                    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
                    data = {
                        "touser": to or "@all",
                        "msgtype": msgtype,
                        "agentid": self.agentid
                    }
                    if msgtype == "text":
                        data["text"] = {"content": message}
                    elif msgtype == "markdown":
                        data["markdown"] = {"content": message}
                
                # 发送请求，5秒超时
                async with session.post(url, json=data, timeout=5) as response:
                    result = await response.json()
                    if result.get("errcode") == 0:
                        return result
                    else:
                        logger.warning(f"发送消息失败 (尝试 {retry + 1}/{max_retries}): {result}")
                        if retry < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            continue
                        return result
            except Exception as e:
                logger.error(f"发送消息异常 (尝试 {retry + 1}/{max_retries}): {e}")
                if retry < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return {"errcode": 500, "errmsg": str(e)}

wechat_service = WeChatService()

