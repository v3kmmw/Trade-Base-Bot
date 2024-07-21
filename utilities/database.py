import aiosqlite
import shortuuid
import discord
import json
from typing import List

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

async def add_user(db: aiosqlite.Connection, user_id: int, invited_by: int = None):
    try:
        # Check if the user ID exists in the table
        check_query = """
            SELECT id FROM users WHERE id = ?
        """
        async with db.execute(check_query, (user_id,)) as cursor:
            row = await cursor.fetchone()

        if row is None:
            # Default values for new users
            balance = 500
            invites = 0
            fake_invites = 0
            tickets = '[]'
            insert_query = """
                INSERT INTO users (id, balance, invited_by, invites, fake_invites, tickets)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            insert_params = (user_id, balance, invited_by, invites, fake_invites, tickets)
            await db.execute(insert_query, insert_params)
            await db.commit()
            print(f"User ID {user_id} inserted with default values.")
        else:
            return
    except Exception as e:
        print(f"Error adding user ID {user_id}: {e}")
        await db.rollback()


async def get_user(db: aiosqlite.Connection, user: discord.User):
    try:
        query = """
            SELECT balance, invited_by, invites, fake_invites, tickets
            FROM users
            WHERE id = ?
        """
        params = (user.id,)

        async with db.execute(query, params) as cursor:
            row = await cursor.fetchone()

        if row is None:
            print(f"User ID {user.id} not found.")
            return None

        # Unpack the row data
        balance, invited_by, invites, fake_invites, tickets = row

        # Optionally process or return the data as a dictionary or a custom object
        user_data = {
            'id': user.id,
            'balance': balance,
            'invited_by': invited_by,
            'invites': invites,
            'fake_invites': fake_invites,
            'tickets': tickets
        }

        return user_data

    except Exception as e:
        print(f"Error retrieving user ID {user.id}: {e}")
        return None


async def update_user(db: aiosqlite.Connection, user_id: int, **kwargs):
    try:
        # Create a list of columns to update and their new values
        set_clause = ", ".join(f"{column} = ?" for column in kwargs.keys())
        params = list(kwargs.values())
        params.append(user_id)  # Append the user_id to the end of the parameters list

        # Update query
        query = f"""
            UPDATE users
            SET {set_clause}
            WHERE id = ?
        """

        async with db.execute(query, params) as cursor:
            await db.commit()

        print(f"User ID {user_id} updated with values: {kwargs}")

    except Exception as e:
        print(f"Error updating user ID {user_id}: {e}")
        await db.rollback()

async def create_scammer_report(db: aiosqlite.Connection, user_id: int, reporter: int, proof: List[str]):
    try:
        # Create a unique report ID
        report_id = shortuuid.ShortUUID().random(length=15)

        # Insert the report into the database
        async with db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO reports (code, user_id, reporter, proof)
                VALUES (?, ?, ?, ?)
            """, (report_id, user_id, reporter, json.dumps(proof)))
        
        await db.commit()
        return report_id
    
    except Exception as e:
        print(f"Error creating scammer report: {e}")
        return None

async def create_report_verification(db: aiosqlite.Connection, **kwargs):
    try:
        # Prepare columns and values for the insertion
        columns = ", ".join(kwargs.keys())
        placeholders = ", ".join("?" for _ in kwargs)
        values = list(kwargs.values())

        # Insert query
        query = f"""
            INSERT INTO reportverification ({columns})
            VALUES ({placeholders})
        """

        async with db.cursor() as cursor:
            await cursor.execute(query, values)
        
        await db.commit()
        print(f"Report created with values: {kwargs}")

    except Exception as e:
        print(f"Error creating report: {e}")
        await db.rollback()
        return None

    return True

async def get_report_verification(db: aiosqlite.Connection, code: str):
    try:
        query = """
            SELECT *
            FROM reportverification
            WHERE code = ?
        """
        params = (code,)

        async with db.execute(query, params) as cursor:
            result = await cursor.fetchone()
            if result:
                proof_json = result[6]
                # Parse the JSON string to a Python list
                proof = json.loads(proof_json) if proof_json else []
                return {
                    'code': result[0],
                    'status': result[1],
                    'reporter': result[2],
                    'scammer': result[3],
                    'public': result[4],
                    'message_link': result[5],
                    'proof': proof,
                    'date': result[7]
                }
            else:
                return None
    except Exception as e:
        print(f"Error fetching report: {e}")
        return None
async def sync_invites(db: aiosqlite.Connection, invites):
    try:
        async with db.cursor() as cursor:
            for invite in invites:
                creator_id = invite.inviter.id if invite.inviter else None
                query = """
                    INSERT INTO invitecodes (code, creator, uses)
                    VALUES (?, ?, ?)
                    ON CONFLICT(code) DO UPDATE SET
                    creator = excluded.creator,
                    uses = excluded.uses
                """                
                params = (invite.code, creator_id, invite.uses)
                await cursor.execute(query, params)

        await db.commit()
        print("Invites synchronized successfully.")
    except Exception as e:
        print(f"Error synchronizing invites: {e}")
        await db.rollback()

async def update_pending_proof_public(db: aiosqlite.Connection, code, public):
    try:
        query = """
            UPDATE reportverification
            SET public = ?
            WHERE code = ?
        """
        params = (public, code,)
        async with db.cursor() as cursor:
            await cursor.execute(query, params)
            await db.commit()
        
        print(f"Public status updated for report code: {code}")
    except Exception as e:
        print(f"Error updating public status: {e}")
        await db.rollback()


async def update_pending_proof(db: aiosqlite.Connection, code, proof):
    try:
        query = """
            UPDATE reportverification
            SET proof = ?
            WHERE code = ?
        """
        params = (json.dumps(proof), code,)
        async with db.cursor() as cursor:
            await cursor.execute(query, params)
            await db.commit()
        
        print(f"Proof updated for report code: {code}")

    except Exception as e:
        print(f"Error updating proof: {e}")
        await db.rollback()

async def handle_report_upload(db: aiosqlite.Connection, message_link: str):
    try:
        query = """
            UPDATE reportverification
            SET status = 'Proof Uploaded!'
            WHERE message_link = ?
        """
        params = (message_link,)

        async with db.cursor() as cursor:
            await cursor.execute(query, params)
            await db.commit()

        print(f"Report status updated to 'Proof Uploaded!' for message link: {message_link}")
    except Exception as e:
        print(f"Error updating report status: {e}")
        await db.rollback()

async def verify_report(db: aiosqlite.Connection, code: str):
    try:
        query = """
            SELECT message_link
            FROM reportverification
            WHERE code = ?
        """
        params = (code,)
        
        async with db.execute(query, params) as cursor:
            result = await cursor.fetchone()
            
            if result is None:
                return False
            
            message_link = result[0]
            await handle_report_upload(db, message_link)            
            return True

    except Exception as e:
        print(f"Error verifying report: {e}")
        return False, None
    
async def get_scammer(db: aiosqlite.Connection, scammer: str):
    try:
        query = """
            SELECT code, status, reporter, scammer, public, message_link, proof, date
            FROM reports
            WHERE scammer = ?
        """
        params = (scammer,)
        async with db.execute(query, params) as cursor:
            result = await cursor.fetchall()
            if not result:
                print("Scammer does not exist in reports table.")
                return None
            # Create a list of dictionaries for each report
            reports = [
                {
                    'code': row[0],
                    'status': row[1],
                    'reporter': row[2],
                    'scammer': row[3],
                    'public': row[4],
                    'message_link': row[5],
                    'proof': json.loads(row[6]),
                    'date': row[7]
                }
                for row in result
            ]
            return reports
    except Exception as e:
        print(f"Error fetching scammer: {e}")
        return None

async def get_report(db: aiosqlite.Connection, code: str):
    try:
        query = """
            SELECT code, status, reporter, scammer, public, message_link, proof, date
            FROM reports
            WHERE code = ?
        """
        params = (code,)
        async with db.execute(query, params) as cursor:
            result = await cursor.fetchone()
            if result is None:
                print("Code does not exist in reports table.")
                return False
            return {
                'code': result[0],
                'status': result[1],
                'reporter': result[2],
               'scammer': result[3],
                'public': result[4],
               'message_link': result[5],
                'proof': json.loads(result[6]),
                'date': result[7]
            }
    except Exception as e:
        print(f"Error fetching report: {e}")
        return None
        

async def create_report(db: aiosqlite.Connection, code: str):
    try:
        # Check if the code exists in the reportverification table and get the associated data
        query = """
            SELECT code, status, reporter, scammer, public, message_link, proof, date
            FROM reportverification
            WHERE code = ?
        """
        params = (code,)
        async with db.execute(query, params) as cursor:
            result = await cursor.fetchone()
            if result is None:
                print("Code does not exist in reportverification table.")
                return False

        # Insert the retrieved data into the reports table
        insert_query = """
            INSERT INTO reports (code, status, reporter, scammer, public, message_link, proof, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        await db.execute(insert_query, result)
        await db.commit()
        return True

    except Exception as e:
        print(f"Error creating report: {e}")
        return False


async def create_code(db: aiosqlite.Connection, user, amount):
    try:
        code = shortuuid.ShortUUID().random(length=10)
        insert_query = """
            INSERT INTO codes (code, amount, owner)
            VALUES (?,?,?)
        """
        user_id = user.id
        await add_user(db, user_id)
        insert_params = (code, amount, user_id)
        await db.execute(insert_query, insert_params)
        await db.commit()
        return code
    except Exception as e:
        print(f"Error creating code: {e}")
        await db.rollback()
        return None
    