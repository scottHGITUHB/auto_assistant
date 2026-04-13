from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from models import db, Reminder

router = APIRouter()


class ReminderCreate(BaseModel):
    user_id: str
    content: str
    remind_at: str


class ReminderResponse(BaseModel):
    id: int
    user_id: str
    content: str
    remind_at: str
    is_done: bool
    created_at: str


@router.get("", response_model=List[ReminderResponse])
async def get_reminders():
    reminders = db.session.query(Reminder).all()
    return [
        ReminderResponse(
            id=reminder.id,
            user_id=reminder.user_id,
            content=reminder.content,
            remind_at=reminder.remind_at,
            is_done=reminder.is_done,
            created_at=reminder.created_at.isoformat()
        )
        for reminder in reminders
    ]


@router.post("", response_model=ReminderResponse)
async def create_reminder(reminder: ReminderCreate):
    new_reminder = Reminder(
        user_id=reminder.user_id,
        content=reminder.content,
        remind_at=reminder.remind_at,
        is_done=False
    )
    db.session.add(new_reminder)
    db.session.commit()
    db.session.refresh(new_reminder)
    return ReminderResponse(
        id=new_reminder.id,
        user_id=new_reminder.user_id,
        content=new_reminder.content,
        remind_at=new_reminder.remind_at,
        is_done=new_reminder.is_done,
        created_at=new_reminder.created_at.isoformat()
    )


@router.put("/{reminder_id}/done")
async def mark_reminder_done(reminder_id: int):
    existing_reminder = db.session.query(Reminder).filter_by(id=reminder_id).first()
    if not existing_reminder:
        raise HTTPException(status_code=404, detail="提醒不存在")
    
    existing_reminder.is_done = True
    db.session.commit()
    db.session.refresh(existing_reminder)
    return ReminderResponse(
        id=existing_reminder.id,
        user_id=existing_reminder.user_id,
        content=existing_reminder.content,
        remind_at=existing_reminder.remind_at,
        is_done=existing_reminder.is_done,
        created_at=existing_reminder.created_at.isoformat()
    )
