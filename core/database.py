from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from secure_vault.core.config import get_settings
import databases

settings = get_settings()

# Create database URL
if settings.database_type == "sqlite":
    DATABASE_URL = f"sqlite+aiosqlite:///{settings.data_dir}/{settings.database_name}"
elif settings.database_type == "postgresql":
    DATABASE_URL = f"postgresql+asyncpg://{settings.database_user}:{settings.database_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}"
elif settings.database_type == "mysql":
    DATABASE_URL = f"mysql+aiomysql://{settings.database_user}:{settings.database_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}"

# SQLAlchemy specific setup
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Database instance
database = databases.Database(DATABASE_URL)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
