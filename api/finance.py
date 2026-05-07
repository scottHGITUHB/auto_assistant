from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from models import get_db, FinanceRecord
from sqlalchemy.orm import Session
from datetime import datetime

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
    records = session.query(FinanceRecord).order_by(FinanceRecord.record_date.desc()).all()
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


@router.get("/monthly-stats")
async def get_monthly_stats(session: Session = Depends(get_db)):
    """Get monthly financial statistics grouped by year and month"""
    records = session.query(FinanceRecord).all()

    # Group by year-month
    monthly_data = {}
    yearly_data = {}

    for record in records:
        year_month = record.record_date[:7]  # YYYY-MM
        year = record.record_date[:4]  # YYYY

        if year_month not in monthly_data:
            monthly_data[year_month] = {
                "income": 0,
                "expense": 0,
                "balance": 0,
                "categories": {}
            }

        monthly_data[year_month][record.type] += record.amount

        # Category breakdown
        if record.type == "expense":
            if record.category not in monthly_data[year_month]["categories"]:
                monthly_data[year_month]["categories"][record.category] = 0
            monthly_data[year_month]["categories"][record.category] += record.amount

        # Yearly aggregation
        if year not in yearly_data:
            yearly_data[year] = {
                "income": 0,
                "expense": 0,
                "balance": 0,
                "months": []
            }
        yearly_data[year][record.type] += record.amount

    # Calculate balances and savings rates
    for year_month in monthly_data:
        data = monthly_data[year_month]
        data["balance"] = data["income"] - data["expense"]
        data["savings_rate"] = (data["balance"] / data["income"] * 100) if data["income"] > 0 else 0
        data["budget"] = data["income"] * 0.8
        data["budget_remaining"] = data["budget"] - data["expense"]

    for year in yearly_data:
        data = yearly_data[year]
        data["balance"] = data["income"] - data["expense"]
        data["savings_rate"] = (data["balance"] / data["income"] * 100) if data["income"] > 0 else 0

    # Sort by date
    sorted_months = sorted(monthly_data.keys(), reverse=True)
    sorted_years = sorted(yearly_data.keys(), reverse=True)

    return {
        "monthly": {k: monthly_data[k] for k in sorted_months},
        "yearly": {k: yearly_data[k] for k in sorted_years},
        "current_month": datetime.now().strftime("%Y-%m"),
        "current_year": datetime.now().strftime("%Y")
    }


@router.get("/yearly-report/{year}")
async def get_yearly_report(year: str, session: Session = Depends(get_db)):
    """Get detailed yearly financial report"""
    records = session.query(FinanceRecord).filter(
        FinanceRecord.record_date.startswith(year)
    ).all()

    # Monthly breakdown
    months = {}
    category_yearly = {}

    for record in records:
        month = record.record_date[5:7]  # MM

        if month not in months:
            months[month] = {
                "income": 0,
                "expense": 0,
                "balance": 0,
                "categories": {}
            }

        months[month][record.type] += record.amount

        if record.type == "expense":
            if record.category not in months[month]["categories"]:
                months[month]["categories"][record.category] = 0
            months[month]["categories"][record.category] += record.amount

            if record.category not in category_yearly:
                category_yearly[record.category] = 0
            category_yearly[record.category] += record.amount

    # Calculate balances and sort categories
    for month in months:
        data = months[month]
        data["balance"] = data["income"] - data["expense"]
        data["savings_rate"] = (data["balance"] / data["income"] * 100) if data["income"] > 0 else 0

    total_income = sum(r.amount for r in records if r.type == "income")
    total_expense = sum(r.amount for r in records if r.type == "expense")
    total_balance = total_income - total_expense

    # Sort months
    sorted_months = sorted(months.keys())

    return {
        "year": year,
        "total_income": total_income,
        "total_expense": total_expense,
        "total_balance": total_balance,
        "savings_rate": (total_balance / total_income * 100) if total_income > 0 else 0,
        "months": {k: months[k] for k in sorted_months},
        "category_breakdown": dict(sorted(category_yearly.items(), key=lambda x: x[1], reverse=True))
    }
