import os
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# Default: prepstack.db next to this file. Override with DATABASE_URL env var.
_default = f"sqlite+aiosqlite:///{Path(__file__).parent / 'prepstack.db'}"
DATABASE_URL = os.environ.get("DATABASE_URL", _default)

engine = create_async_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
