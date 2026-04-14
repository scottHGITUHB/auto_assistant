from models import db
from models.db import SessionLocal, PushContent, MessageLog
from datetime import datetime

# 初始化数据库
db.init_db()

# 创建会话
session = SessionLocal()

try:
    # 添加测试数据
    # 添加推送数据
    push1 = PushContent(
        title='测试推送1',
        content='测试内容1',
        push_time='08:30',
        target_group='全体成员',
        is_active=True,
        created_at=datetime.now()
    )
    
    push2 = PushContent(
        title='测试推送2',
        content='测试内容2',
        push_time='12:00',
        target_group='管理层',
        is_active=True,
        created_at=datetime.now()
    )
    
    # 添加消息日志数据
    log1 = MessageLog(
        direction='in',
        content='测试消息1',
        response='测试响应1',
        status='success',
        created_at=datetime.now()
    )
    
    log2 = MessageLog(
        direction='out',
        content='测试消息2',
        response='',
        status='success',
        created_at=datetime.now()
    )
    
    log3 = MessageLog(
        direction='in',
        content='测试消息3',
        response='测试响应3',
        status='success',
        created_at=datetime.now()
    )
    
    # 添加到会话
    session.add_all([push1, push2, log1, log2, log3])
    
    # 提交事务
    session.commit()
    
    print('测试数据添加成功')
    print('PushContent表记录数:', session.query(PushContent).count())
    print('MessageLog表记录数:', session.query(MessageLog).count())
    
except Exception as e:
    print(f'添加测试数据失败: {e}')
    session.rollback()
finally:
    # 关闭会话
    session.close()
