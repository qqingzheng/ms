import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import asynccontextmanager

DATABASE_URL = f"mysql+asyncmy://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DATABASE')}"

engine = create_async_engine(DATABASE_URL, echo=True)

async_session_factory = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

def get_base():
    return declarative_base()

async def remake_db(Base):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def init_db(Base):
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def get_session():
    async_session = async_session_factory()
    try:
        yield async_session
    finally:
        await async_session.close()