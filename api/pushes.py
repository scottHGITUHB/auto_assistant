from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from models import db, PushContent

router = APIRouter()


class PushContentCreate(BaseModel):
    title: str
    content: str
    push_time: str
    target_group: str
    is_active: bool = True


class PushContentUpdate(BaseModel):
    title: str
    content: str
    push_time: str
    target_group: str
    is_active: bool


class PushContentResponse(BaseModel):
    id: int
    title: str
    content: str
    push_time: str
    target_group: str
    is_active: bool
    created_at: str


@router.get("", response_model=List[PushContentResponse])
async def get_pushes():
    pushes = db.session.query(PushContent).all()
    return [
        PushContentResponse(
            id=push.id,
            title=push.title,
            content=push.content,
            push_time=push.push_time,
            target_group=push.target_group,
            is_active=push.is_active,
            created_at=push.created_at.isoformat()
        )
        for push in pushes
    ]


@router.post("", response_model=PushContentResponse)
async def create_push(push: PushContentCreate):
    new_push = PushContent(
        title=push.title,
        content=push.content,
        push_time=push.push_time,
        target_group=push.target_group,
        is_active=push.is_active
    )
    db.session.add(new_push)
    db.session.commit()
    db.session.refresh(new_push)
    return PushContentResponse(
        id=new_push.id,
        title=new_push.title,
        content=new_push.content,
        push_time=new_push.push_time,
        target_group=new_push.target_group,
        is_active=new_push.is_active,
        created_at=new_push.created_at.isoformat()
    )


@router.put("/{push_id}", response_model=PushContentResponse)
async def update_push(push_id: int, push: PushContentUpdate):
    existing_push = db.session.query(PushContent).filter_by(id=push_id).first()
    if not existing_push:
        raise HTTPException(status_code=404, detail="推送内容不存在")
    
    existing_push.title = push.title
    existing_push.content = push.content
    existing_push.push_time = push.push_time
    existing_push.target_group = push.target_group
    existing_push.is_active = push.is_active
    
    db.session.commit()
    db.session.refresh(existing_push)
    return PushContentResponse(
        id=existing_push.id,
        title=existing_push.title,
        content=existing_push.content,
        push_time=existing_push.push_time,
        target_group=existing_push.target_group,
        is_active=existing_push.is_active,
        created_at=existing_push.created_at.isoformat()
    )


@router.delete("/{push_id}")
async def delete_push(push_id: int):
    existing_push = db.session.query(PushContent).filter_by(id=push_id).first()
    if not existing_push:
        raise HTTPException(status_code=404, detail="推送内容不存在")
    
    db.session.delete(existing_push)
    db.session.commit()
    return {"status": "success"}
