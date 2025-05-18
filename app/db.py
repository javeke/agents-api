from sqlalchemy.orm import sessionmaker, declarative_base
from .settings import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

SQLALCHEMY_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=settings.DEBUG)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()
