from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models import db, Admin
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    # 这里简化处理，实际应该使用JWT
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH", "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW")  # 默认密码: admin
    
    if request.username != admin_username:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if not bcrypt.checkpw(request.password.encode('utf-8'), admin_password_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 简化返回，实际应该生成JWT token
    return LoginResponse(access_token="mock_token", token_type="bearer")
