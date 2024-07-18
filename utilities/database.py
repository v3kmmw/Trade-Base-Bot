import aiosqlite

async def get_prefix(db: aiosqlite.Connection, guild_id=None):
    try:
        query = """
            SELECT prefix
            FROM guilds
        """
        params = ()
        if guild_id is not None:
            query += " WHERE id = ?"
            params = (guild_id,)  

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            if rows:
                return rows[0][0]
            else:
                return '-'
    except Exception as e:
        print(f"Error fetching guild prefix: {e}")
        return '-'

async def set_prefix(db: aiosqlite.Connection, guild, new_prefix: str):
    print(f"Setting prefix for guild {guild.id} to {new_prefix}")
    try:
        # Check if the guild ID exists in the table
        guild_id = guild.id
        check_query = """
            SELECT id FROM guilds WHERE id = ?
        """
        async with db.execute(check_query, (guild_id,)) as cursor:
            row = await cursor.fetchone()
        
        if row is None:
            # Guild ID not found, insert a new record
            insert_query = """
                INSERT INTO guilds (id, prefix)
                VALUES (?, ?)
            """
            insert_params = (guild_id, new_prefix)
            await db.execute(insert_query, insert_params)
            await db.commit()
            print(f"Guild ID {guild_id} inserted with prefix {new_prefix}")
        else:
            # Guild ID found, update prefix
            update_query = """
                UPDATE guilds
                SET prefix = ?
                WHERE id = ?
            """
            update_params = (new_prefix, guild_id)
            await db.execute(update_query, update_params)
            await db.commit()
            print(f"Prefix updated successfully for guild ID {guild_id}")
    except Exception as e:
        print(f"Error updating prefix for guild ID {guild_id}: {e}")
        await db.rollback()