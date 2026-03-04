from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import text
from .config import settings


# Base class all models inherit from
class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "debug",
    future=True,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Create all tables on startup"""
    import app.models
    async with engine.begin() as conn:
        def log_and_create(sync_conn):
            from sqlalchemy import event
            from sqlalchemy.sql.schema import Table
            created = []
            def before_create(target, connection, **kw):
                if isinstance(target, Table):
                    created.append(target.name)
            event.listen(Base.metadata, "before_create", before_create)
            Base.metadata.create_all(sync_conn)
            if created:
                print(f"✅ Tables created: {', '.join(created)}")
            else:
                print("✅ All tables already exist")
        await conn.run_sync(log_and_create)


async def check_db_connection():
    """Confirm DB is reachable — called at startup."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise


async def get_session() -> AsyncSession:
    """FastAPI dependency — yields a DB session per request."""
    async with AsyncSessionLocal() as session:
        yield session