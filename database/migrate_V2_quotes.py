import asyncio
import datetime as dt
import os
import sys

import asqlite
from dotenv import load_dotenv

load_dotenv()

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from models.db import QuotesDB
from models.schema import Base, Quote


async def migrate_data():
    old_database_path = "AbetDatabase.db"  # Update this with your database path
    new_database_path = os.getenv(
        "DB_MIGRATION_URI"
    )  # Update this with your database path
    print(new_database_path)
    new_database = QuotesDB(new_database_path)

    async with asqlite.connect(old_database_path) as old_db:
        async with old_db.cursor() as old_cursor:
            await old_cursor.execute(
                "SELECT id, quote, quote_by, added_by, timestamp FROM quotes"
            )
            old_rows = await old_cursor.fetchall()
            # print(old_rows[0][2])

        # async with asqlite.connect(new_database_path) as new_db:
        #     async with new_db.cursor() as new_cursor:
        #         for row in old_rows:
        #             await new_cursor.execute(
        #                 """
        #                 INSERT INTO quotes (id, quote, quote_by, added_by, timestamp)
        #                 VALUES (?, ?, ?, ?, ?)
        #             """,
        #                 (row[0], row[1], waikei_id, row[2], row[3]),
        #             )
        #         await new_db.commit()

        await new_database._insert_objects(
            [
                Quote(
                    id=row[0],
                    quote=row[1],
                    quote_by=str(row[2]),
                    added_by=str(row[3]),
                    timestamp=dt.datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S"),
                )
                for row in old_rows
            ]
        )


# async def delete_old_table():
#     database_path = "AbetDatabase.db"  # Update this with your database path

#     async with asqlite.connect(database_path) as db:
#         async with db.cursor() as cursor:
#             await cursor.execute("DROP TABLE IF EXISTS quotes_waikei")
#             await db.commit()


if __name__ == "__main__":

    asyncio.run(migrate_data())
    # asyncio.run(delete_old_table())
