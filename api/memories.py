from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from models import get_db, Memory
from sqlalchemy.orm import Session

router = APIRouter()


class MemoryCreate(BaseModel):
    user_id: str
    content: str
    category: str = "default"


class MemoryResponse(BaseModel):
    id: int
    user_id: str
    content: str
    category: str
    created_at: str


@router.get("", response_model=List[MemoryResponse])
async def get_memories(session: Session = Depends(get_db)):
    memories = session.query(Memory).all()
    return [
        MemoryResponse(
            id=memory.id,
            user_id=memory.user_id,
            content=memory.content,
            category=memory.category,
            created_at=memory.created_at.isoformat()
        )
        for memory in memories
    ]


@router.post("", response_model=MemoryResponse)
async def create_memory(memory: MemoryCreate, session: Session = Depends(get_db)):
    new_memory = Memory(
        user_id=memory.user_id,
        content=memory.content,
        category=memory.category
    )
    session.add(new_memory)
    session.commit()
    session.refresh(new_memory)
    return MemoryResponse(
        id=new_memory.id,
        user_id=new_memory.user_id,
        content=new_memory.content,
        category=new_memory.category,
        created_at=new_memory.created_at.isoformat()
    )


@router.delete("/{memory_id}")
async def delete_memory(memory_id: int, session: Session = Depends(get_db)):
    existing_memory = session.query(Memory).filter_by(id=memory_id).first()
    if not existing_memory:
        raise HTTPException(status_code=404, detail="记忆不存在")
    
    session.delete(existing_memory)
    session.commit()
    return {"status": "success"}
