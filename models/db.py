from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)


class PushContent(Base):
    __tablename__ = "push_contents"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    content = Column(Text)
    push_time = Column(String(50))
    target_group = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CrawlerTask(Base):
    __tablename__ = "crawler_tasks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    url = Column(String(500))
    selector = Column(Text)
    cron_expr = Column(String(100))
    last_result = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255))
    content = Column(Text)
    category = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255))
    content = Column(Text)
    remind_at = Column(String(100))
    is_done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class FinanceRecord(Base):
    __tablename__ = "finance_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255))
    type = Column(String(50))  # income 或 expense
    amount = Column(Float)
    category = Column(String(100))
    note = Column(Text)
    record_date = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class MessageLog(Base):
    __tablename__ = "message_logs"
    id = Column(Integer, primary_key=True, index=True)
    direction = Column(String(50))  # in 或 out
    content = Column(Text)
    response = Column(Text)
    status = Column(String(50))
    error_msg = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Setting(Base):
    __tablename__ = "settings"
    key = Column(String(255), primary_key=True)
    value = Column(Text)
    description = Column(Text)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    """为每个请求创建新的数据库会话"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class Database:
    def __init__(self):
        self.session = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def init_db(self):
        Base.metadata.create_all(bind=engine)

db = Database()
