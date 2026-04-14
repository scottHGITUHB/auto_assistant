from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from models import get_db, FinanceRecord
from sqlalchemy.orm import Session

router = APIRouter()


class FinanceRecordCreate(BaseModel):
    user_id: str
    type: str  # income 或 expense
    amount: float
    category: str
    note: str = ""
    record_date: str


class FinanceRecordResponse(BaseModel):
    id: int
    user_id: str
    type: str
    amount: float
    category: str
    note: str
    record_date: str
    created_at: str


class FinanceStatsResponse(BaseModel):
    total_income: float
    total_expense: float
    balance: float
    category_stats: dict
    category_expenses: dict


@router.get("", response_model=List[FinanceRecordResponse])
async def get_finance_records(session: Session = Depends(get_db)):
    records = session.query(FinanceRecord).all()
    return [
        FinanceRecordResponse(
            id=record.id,
            user_id=record.user_id,
            type=record.type,
            amount=record.amount,
            category=record.category,
            note=record.note,
            record_date=record.record_date,
            created_at=record.created_at.isoformat()
        )
        for record in records
    ]


@router.post("", response_model=FinanceRecordResponse)
async def create_finance_record(record: FinanceRecordCreate, session: Session = Depends(get_db)):
    new_record = FinanceRecord(
        user_id=record.user_id,
        type=record.type,
        amount=record.amount,
        category=record.category,
        note=record.note,
        record_date=record.record_date
    )
    session.add(new_record)
    session.commit()
    session.refresh(new_record)
    return FinanceRecordResponse(
        id=new_record.id,
        user_id=new_record.user_id,
        type=new_record.type,
        amount=new_record.amount,
        category=new_record.category,
        note=new_record.note,
        record_date=new_record.record_date,
        created_at=new_record.created_at.isoformat()
    )


@router.get("/stats", response_model=FinanceStatsResponse)
async def get_finance_stats(session: Session = Depends(get_db)):
    records = session.query(FinanceRecord).all()
    
    total_income = sum(r.amount for r in records if r.type == "income")
    total_expense = sum(r.amount for r in records if r.type == "expense")
    balance = total_income - total_expense
    
    category_stats = {}
    for record in records:
        if record.category not in category_stats:
            category_stats[record.category] = {"income": 0, "expense": 0}
        category_stats[record.category][record.type] += record.amount
    
    # 转换格式以匹配前端
    category_expenses = {}
    category_income = {}
    for cat, stats in category_stats.items():
        category_expenses[cat] = stats["expense"]
        category_income[cat] = stats["income"]
    
    return FinanceStatsResponse(
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        category_stats=category_stats,
        category_expenses=category_expenses
    )
