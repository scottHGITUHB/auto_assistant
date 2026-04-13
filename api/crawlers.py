from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from models import db, CrawlerTask
from services import crawler_service

router = APIRouter()


class CrawlerTaskCreate(BaseModel):
    name: str
    url: str
    selector: str
    cron_expr: str
    is_active: bool = True


class CrawlerTaskResponse(BaseModel):
    id: int
    name: str
    url: str
    selector: str
    cron_expr: str
    last_result: str
    is_active: bool
    created_at: str


@router.get("", response_model=List[CrawlerTaskResponse])
async def get_crawlers():
    crawlers = db.session.query(CrawlerTask).all()
    return [
        CrawlerTaskResponse(
            id=crawler.id,
            name=crawler.name,
            url=crawler.url,
            selector=crawler.selector,
            cron_expr=crawler.cron_expr,
            last_result=crawler.last_result,
            is_active=crawler.is_active,
            created_at=crawler.created_at.isoformat()
        )
        for crawler in crawlers
    ]


@router.post("", response_model=CrawlerTaskResponse)
async def create_crawler(crawler: CrawlerTaskCreate):
    new_crawler = CrawlerTask(
        name=crawler.name,
        url=crawler.url,
        selector=crawler.selector,
        cron_expr=crawler.cron_expr,
        is_active=crawler.is_active
    )
    db.session.add(new_crawler)
    db.session.commit()
    db.session.refresh(new_crawler)
    return CrawlerTaskResponse(
        id=new_crawler.id,
        name=new_crawler.name,
        url=new_crawler.url,
        selector=new_crawler.selector,
        cron_expr=new_crawler.cron_expr,
        last_result=new_crawler.last_result,
        is_active=new_crawler.is_active,
        created_at=new_crawler.created_at.isoformat()
    )


@router.post("/{crawler_id}/run")
async def run_crawler(crawler_id: int):
    crawler = db.session.query(CrawlerTask).filter_by(id=crawler_id).first()
    if not crawler:
        raise HTTPException(status_code=404, detail="爬虫任务不存在")
    
    result = crawler_service.run_crawler(crawler)
    return result
