import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from models.db import BaseDBManager
from models.engine import EngineSingleton


async def migrate_data() -> None:
    database_uri = os.getenv("DB_MIGRATION_URI") or os.getenv("DB_URI", "")
    if not database_uri:
        raise ValueError("DB_MIGRATION_URI or DB_URI must be set.")

    engine = EngineSingleton.get_engine(database_uri)
    manager = BaseDBManager(engine)
    await manager._create_tables()
    await manager.close()


if __name__ == "__main__":
    asyncio.run(migrate_data())
