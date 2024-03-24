import asyncio

import asqlite


async def migrate_data():
    old_database_path = "AbetDatabase.db"  # Update this with your database path
    new_database_path = (
        "AbetDatabase.db"  # This can be the same if you're upgrading in-place
    )
    waikei_id = 192192501187215361  # Replace with Waikei's actual Discord user ID

    async with asqlite.connect(old_database_path) as old_db:
        async with old_db.cursor() as old_cursor:
            await old_cursor.execute(
                "SELECT id, quote, added_by, timestamp FROM quotes_waikei"
            )
            old_rows = await old_cursor.fetchall()
            # print(old_rows[0][2])

    async with asqlite.connect(new_database_path) as new_db:
        async with new_db.cursor() as new_cursor:
            for row in old_rows:
                await new_cursor.execute(
                    """
                    INSERT INTO quotes (id, quote, quote_by, added_by, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (row[0], row[1], waikei_id, row[2], row[3]),
                )
            await new_db.commit()


async def delete_old_table():
    database_path = "AbetDatabase.db"  # Update this with your database path

    async with asqlite.connect(database_path) as db:
        async with db.cursor() as cursor:
            await cursor.execute("DROP TABLE IF EXISTS quotes_waikei")
            await db.commit()


if __name__ == "__main__":

    # asyncio.run(migrate_data())
    asyncio.run(delete_old_table())
