from contextlib import asynccontextmanager
from typing import AsyncGenerator
from app.db import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.mail.mail_service import MailService
from app.services.report_processing.report_service import ReportService

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

@asynccontextmanager
async def get_db_context():
    async with SessionLocal() as session:
        yield session

def get_mail_client() -> MailService:
    return MailService()

def get_report_service() -> ReportService:
    return ReportService()
