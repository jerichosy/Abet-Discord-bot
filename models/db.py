from typing import Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio.session import async_sessionmaker

from .schema import Base, Quote, Tag


class BaseDBManager:
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine
        self.SessionLocal = async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)

    async def _create_tables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _insert_objects(self, objects: list[Base]):
        async with self.SessionLocal() as session:
            async with session.begin():
                session.add_all(objects)

    async def close(self) -> None:
        await self.engine.dispose()


class QuotesManager(BaseDBManager):
    async def find_if_quote_exists_by_quote(self, quote: str, member_id: int) -> Quote | None:
        async with self.SessionLocal() as session:
            stmt = select(Quote).where(Quote.quote.ilike(quote)).where(Quote.quote_by.ilike(str(member_id)))
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def find_random_quote(self, member_id: int) -> Quote | None:
        async with self.SessionLocal() as session:
            stmt = select(Quote).where(Quote.quote_by.ilike(str(member_id))).order_by(func.random()).limit(1)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def insert_quote(self, quote: str, quote_by: int, added_by: int) -> int:
        new_quote = Quote(quote=quote, quote_by=str(quote_by), added_by=str(added_by))
        # print(f"Adding quote: {new_quote}")  # doesn't have id field
        await self._insert_objects([new_quote])
        # print(f"Added quote: {new_quote}")  # now has id field
        # print(f"Added quote id: {new_quote.id}, type: {type(new_quote.id)}")
        return new_quote.id

    async def find_quotes_by_member_id(self, quote_by: int, page: int, per_page: int) -> Sequence[Quote]:
        async with self.SessionLocal() as session:
            stmt = (
                select(Quote)
                .where(Quote.quote_by.ilike(str(quote_by)))
                .order_by(Quote.id)
                .limit(per_page)
                .offset((page - 1) * per_page)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def find_quote_by_id(self, quote_id: int) -> Quote | None:
        async with self.SessionLocal() as session:
            stmt = select(Quote).where(Quote.id == quote_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def delete_quote_by_id(self, quote_id: int) -> None:
        async with self.SessionLocal() as session:
            async with session.begin():
                stmt = delete(Quote).where(Quote.id == quote_id)
                await session.execute(stmt)


class TagsManager(BaseDBManager):
    async def find_tag_by_name(self, name: str) -> Tag | None:
        async with self.SessionLocal() as session:
            stmt = select(Tag).where(Tag.name.ilike(name))
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def insert_tag(self, name: str, content: str, owner: int) -> int:
        new_tag = Tag(name=name, content=content, owner=str(owner))
        await self._insert_objects([new_tag])
        return new_tag.id

    async def find_tags_by_user_id(self, owner: int) -> Sequence[Tag]:
        async with self.SessionLocal() as session:
            stmt = select(Tag).where(Tag.owner.ilike(str(owner))).order_by(Tag.id)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def delete_tag_by_name(self, name: str) -> None:
        async with self.SessionLocal() as session:
            async with session.begin():
                stmt = delete(Tag).where(Tag.name == name)
                await session.execute(stmt)
