from datetime import datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio.session import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    owner: Mapped[str] = mapped_column()
    timestamp: Mapped[datetime] = mapped_column(server_default=func.now())

    def __repr__(self) -> str:
        return f"Tag(id={self.id!r}, name={self.name!r}, content={self.content!r}, owner={self.owner!r}, timestamp={self.timestamp!r})"
