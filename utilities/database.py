import aiosqlite

async def get_prefix(db: aiosqlite.Connection):
    try:
        query = """
            SELECT prefix
            FROM prefix
        """
        params = ()

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            if rows:
                return rows[0][0]
            else:
                return '='
    except Exception as e:
        return '='

async def set_prefix(db: aiosqlite.Connection, new_prefix: str):
    try:
        # Check if the prefix record exists
        check_query = """
            SELECT prefix FROM prefix
        """
        async with db.execute(check_query) as cursor:
            row = await cursor.fetchone()

        if row is None:
            # No prefix record found, insert a new one
            insert_query = """
                INSERT INTO prefix (prefix)
                VALUES (?)
            """
            insert_params = (new_prefix,)
            await db.execute(insert_query, insert_params)
        else:
            # Prefix record found, update the existing one
            update_query = """
                UPDATE prefix
                SET prefix = ?
            """
            update_params = (new_prefix,)
            await db.execute(update_query, update_params)

        await db.commit()
        print(f"Prefix set to {new_prefix}")
    except Exception as e:
        print(f"Error updating prefix: {e}")
        await db.rollback()

async def add_user(db: aiosqlite.Connection, user_id: int):
    try:
        # Check if the user ID exists in the table
        check_query = """
            SELECT id FROM users WHERE id = ?
        """
        async with db.execute(check_query, (user_id,)) as cursor:
            row = await cursor.fetchone()

        if row is None:
            # User ID not found, insert a new record
            insert_query = """
                INSERT INTO users (id, balance, tickets)
                VALUES (?, 0, '[]')
            """
            insert_params = (user_id,)
            await db.execute(insert_query, insert_params)
            await db.commit()
            print(f"User ID {user_id} inserted with default balance and empty tickets")
        else:
            return 
    except Exception as e:
        print(f"Error adding user ID {user_id}: {e}")
        await db.rollback()