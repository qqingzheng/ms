import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import asynccontextmanager

# 增加连接池和超时配置
DATABASE_URL = f"mysql+asyncmy://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DATABASE')}"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_pre_ping=True,  # 执行前检查连接是否有效
    pool_recycle=3600,  # 1小时后回收连接
    pool_timeout=30,  # 获取连接超时时间
    connect_args={
        "connect_timeout": 10  # 仅保留连接超时参数
    }
)

async_session_factory = sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)

def get_base():
    return declarative_base()

async def remake_db(Base):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def init_db(Base):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager 
async def get_session():
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            raise