from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.ext.asyncio.session import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

class Base(AsyncAttrs, DeclarativeBase):
    pass

class Quote(Base):
    __tablename__ = "quotes"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quote: Mapped[str] = mapped_column()
    quote_by: Mapped[str] = mapped_column()
    added_by: Mapped[str] = mapped_column()
    timestamp: Mapped[datetime] = mapped_column(server_default=func.now())

    def __repr__(self) -> str:
        return f"Quote(id={self.id!r}, quote={self.quote!r}, quote_by={self.quote_by!r}, added_by={self.added_by!r}, timestamp={self.timestamp!r})"
