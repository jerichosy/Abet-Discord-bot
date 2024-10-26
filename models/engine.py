from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class EngineSingleton:
    _engine: AsyncEngine = None

    @classmethod
    def get_engine(cls, uri: str) -> AsyncEngine:
        if cls._engine is None:
            cls._engine = create_async_engine(uri, echo=True, pool_pre_ping=True)
        return cls._engine
