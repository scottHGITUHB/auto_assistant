import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class WeChatService:
    def __init__(self):
        self.corpid = os.getenv("WECHAT_CORPID")
        self.secret = os.getenv("WECHAT_SECRET")
        self.agentid = os.getenv("WECHAT_AGENTID")
        self.webhook_key = os.getenv("WECHAT_WEBHOOK_KEY")
        self.access_token = None
    
    def get_access_token(self):
        if not self.access_token:
            url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corpid}&corpsecret={self.secret}"
            response = requests.get(url)
            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") == 0:
                    self.access_token = result.get("access_token")
        return self.access_token
    
    def send_message(self, message, to=None, msgtype="text"):
        try:
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
                response = requests.post(url, json=data)
            else:
                # 使用企业微信应用发送消息
                access_token = self.get_access_token()
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
                response = requests.post(url, json=data)
            
            return response.json()
        except Exception as e:
            return {"errcode": 500, "errmsg": str(e)}

wechat_service = WeChatService()
