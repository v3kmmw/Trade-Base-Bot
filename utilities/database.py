import aiosqlite
import shortuuid
import discord
import json
from typing import List, Dict, Any
from discord.ext import commands
from datetime import datetime
import random
bot = discord.AutoShardedClient

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

async def add_user(user_id: int, db: aiosqlite.Connection = None, invited_by: int = None):
    connection_provided = db is not None
    
    try:
        # Use the provided database connection or create a new one
        if not connection_provided:
            db = await aiosqlite.connect("./data/database.db")
        
        # Check if the user ID exists in the table
        check_query = "SELECT id FROM users WHERE id = ?"
        async with db.execute(check_query, (user_id,)) as cursor:
            row = await cursor.fetchone()
        
        if row is None:
            # Default values for new users
            balance = 500
            bank = 0
            username = None
            profile_color = '#DEFAULT_COLOR'
            embed_image = None
            premium = False
            message_streak = 0
            messages = 0
            site_theme = "light"
            site_accent_color = "green"
            linked_roblox_account = None
            crew_id = None
            vouches = 0
            scammer_reports = 0
            reports = '[]'
            tickets = '[]'
            invites = 0
            fake_invites = 0

            insert_query = """
                INSERT INTO users (id, username, balance, bank, profile_color, embed_image, premium, 
                                   message_streak, messages, site_theme, site_accent_color, linked_roblox_account, crew_id, vouches, 
                                   scammer_reports, reports, tickets, invited_by, invites, fake_invites)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            insert_params = (user_id, username, balance, bank, profile_color, embed_image, premium,
                             message_streak, messages, site_theme, site_accent_color, linked_roblox_account, crew_id, vouches,
                             scammer_reports, reports, tickets, invited_by, invites, fake_invites)
            
            daily_member_insert_query = """
            INSERT INTO membercount (id, joined_at)
            VALUES (?, ?)
            """
            
            async with db.cursor() as cursor:
                await cursor.execute(insert_query, insert_params)
                await cursor.execute(daily_member_insert_query, (user_id, datetime.now()))
                await db.commit()
                print(f"User ID {user_id} inserted with default values.")
    except Exception as e:
        print(f"Error adding user ID {user_id}: {e}")
    finally:
        if not connection_provided:
            await db.close()
        



async def get_user(db: aiosqlite.Connection, user: discord.User):
    try:
        query = """
            SELECT id, username, balance, bank, invited_by, invites, fake_invites,
                   profile_color, embed_image, premium, message_streak, messages, site_theme, site_accent_color, linked_roblox_account,
                   crew_id, vouches, scammer_reports, tickets, reports
            FROM users
            WHERE id = ?;
        """
        async with db.execute(query, (user.id,)) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        # Use column names for clarity
        user_data = {
            'id': row[0],
            'username': row[1],
            'balance': row[2],
            'bank': row[3],
            'invited_by': row[4],
            'invites': row[5],
            'fake_invites': row[6],
            'profile_color': row[7],
            'embed_image': row[8],
            'premium': row[9],
            'message_streak': row[10],
            'messages': row[11],
            'site_theme': row[12],
            'site_accent_color': row[13],
            'linked_roblox_account': row[14],
            'crew_id': row[15],
            'vouches': row[16],
            'scammer_reports': row[17],
            'tickets': json.loads(row[18]) if row[18] else [],
            'reports': json.loads(row[19]) if row[19] else []
        }
        return user_data
    except Exception as e:
        print(f"Error retrieving user ID {user.id}: {e}")
        return None
    
async def create_unlockable_role(bot: commands.Bot, db: aiosqlite.Connection, name: str, color: discord.Color, requirement: str, requirement_type: str) -> int:
    try:
        # You can use bot here if needed, for example:
        guild = await bot.fetch_guild(1216546896491843664)
        discord_role = await guild.create_role(name=name, color=color)

        query = """
            INSERT INTO unlockable_roles (id, name, requirement, requirement_type)
            VALUES (?, ?, ?, ?)
        """
        async with db.execute(query, (discord_role.id, name, requirement, requirement_type)) as cursor:
            await db.commit()
            return discord_role
    except Exception as e:
        print(f"Error creating unlockable role: {e}")
        await db.rollback()
        return None

async def get_unlockable_roles(db: aiosqlite.Connection) -> List[Dict[str, Any]]:
    try:
        query = """
            SELECT id, name, requirement, requirement_type
            FROM unlockable_roles
        """
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"Error retrieving unlockable roles: {e}")
        return []
    
async def delete_unlockable_role(db: aiosqlite.Connection, role_id):
    try:
        query = """
            DELETE FROM unlockable_roles WHERE id = ?
        """
        async with db.execute(query, (role_id,)) as cursor:
            await db.commit()
            print(f"Unlockable role with ID {role_id} deleted")
    except Exception as e:
        print(f"Error deleting unlockable role with ID {role_id}: {e}")
        await db.rollback()

async def count_message(message: discord.Message):
    try:
        # Define the queries
        update_query = """
            UPDATE users
            SET messages = messages + 1
            WHERE id = ?
        """
        
        insert_query = """
            INSERT INTO messages (id, timestamp)
            VALUES (?, ?)
        """
        user_id = message.author.id
        date_sent = message.created_at
        message_id = message.id
    
        async with aiosqlite.connect("./data/database.db") as db:
                # Update the message count for the user
            await db.execute(update_query, (user_id,))
                
                # Insert a new record into the messages table
                # Assuming 'id' here is a unique message ID; you'll need to adjust this based on your actual schema
            await db.execute(insert_query, (message_id, date_sent))
                
            await db.commit()
    except Exception as e:
        print(f"Error updating messages count or inserting message for User ID {user_id}: {e}")

async def count_message_ext(message_id = int, user_id = int, date_sent = str):
    try:
        update_query = """
            UPDATE users
            SET messages = messages + 1
            WHERE id = ?
        """
        
        insert_query = """
            INSERT INTO messages (id, timestamp)
            VALUES (?, ?)
        """
    
        async with aiosqlite.connect("./data/database.db") as db:
                # Update the message count for the user
            await db.execute(update_query, (user_id,))
                
                # Insert a new record into the messages table
                # Assuming 'id' here is a unique message ID; you'll need to adjust this based on your actual schema
            await db.execute(insert_query, (message_id, date_sent))
                
            await db.commit()
    except Exception as e:
        print(f"Error updating messages count or inserting message for User ID {user_id}: {e}")


async def get_daily_messages(db:aiosqlite.Connection):
    try:
        q = """
            SELECT COUNT(*) as total_messages
            FROM messages
            WHERE timestamp >= datetime('now', '-1 day')
        """
        async with db.execute(q) as c:
            r = await c.fetchone()
            return r[0] 
    except Exception as e:
        print(f"Error retrieving daily messages: {e}")
        return 0

async def get_messages(db: aiosqlite.Connection, user_id):
    try:
        query = """
            SELECT messages
            FROM users
            WHERE id = ?
        """
        async with db.execute(query, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return 0
            return row[0]  # Extract the messages count from the database row
    except Exception as e:
        print(f"Error retrieving messages for User ID {user_id}: {e}")
        return []

async def handle_role_check(db: aiosqlite.Connection, user, bot: commands.Bot):
    try:
        db_user = await get_user(db, user)
        added_roles = []
        if user is None:
            return
        roles = await get_unlockable_roles(db)
        guild = await bot.fetch_guild(1216546896491843664)

        for role in roles:
            discord_role = guild.get_role(int(role['id']))  # Fetch the role once per iteration
            if not discord_role:
                await delete_unlockable_role(db, role['id'])
                continue

            if role['requirement_type'] == 'balance' and db_user['balance'] >= int(role['requirement']):
                if discord_role not in user.roles:
                    await user.add_roles(discord_role)
                    added_roles.append(discord_role)
            elif role['requirement_type'] == 'vouches' and db_user['vouches'] >= int(role['requirement']):
                print(discord_role.name)
                # Add role handling logic if needed
            elif role['requirement_type'] == 'messages':
                print(discord_role.name)
                # Add role handling logic if needed

        return added_roles
    
    except Exception as e:
        print(f"Error handling role check for User ID {user.id}: {e}")
        return None
    
async def get_failed_rob_response(db: aiosqlite.Connection, user: discord.User) -> str:
    try:
        # Fetch all responses from the database
        async with db.execute("SELECT response FROM failed_rob_responses") as cursor:
            responses = [row[0] for row in await cursor.fetchall()]
        
        # Select a random response and format it
        if responses:
            response = random.choice(responses)
            return response.format(user=user.mention)
        return f"You failed to rob {user.mention}"
    except Exception as e:
        print(f"Error fetching failed rob response: {e}")
        # Return a default message if there's an error
        return f"You failed to rob {user.mention}"


async def get_failed_rob_responses(db: aiosqlite.Connection):
    try:
        # Fetch all responses from the database
        async with db.execute("SELECT response FROM failed_rob_responses") as cursor:
            responses = [row[0] for row in await cursor.fetchall()]

        return responses
    except Exception as e:
        print(f"Error fetching failed rob responses: {e}")
        return []  # Return an empty list in case of an error


async def add_failed_rob_response(db: aiosqlite.Connection, response: str):
    try:
        # Insert the new response into the database
        query = "INSERT INTO failed_rob_responses (response) VALUES (?)"
        async with db.execute(query, (response,)) as cursor:
            await db.commit()
            print(f"Added failed rob response: {response}")
            return True
    except Exception as e:
        print(f"Error adding failed rob response: {e}")
        return False

    
async def remove_failed_rob_response(db: aiosqlite.Connection, response_id):
    try:
        # Delete the response from the database
        query = "DELETE FROM failed_rob_responses WHERE id = ?"
        async with db.execute(query, (response_id,)) as cursor:
            await db.commit()
            print(f"Removed failed rob response with ID {response_id}")
            return True
    except Exception as e:
        print(f"Error removing failed rob response with ID {response_id}: {e}")
        return False

async def update_user(db: aiosqlite.Connection, user_id: int, **kwargs):
    try:
        # Check if the user exists
        check_query = "SELECT id FROM users WHERE id = ?"
        async with db.execute(check_query, (user_id,)) as cursor:
            if await cursor.fetchone() is None:
                print(f"User ID {user_id} does not exist.")
                return False

        # Validate input: ensure all keys in kwargs are valid column names
        valid_columns = {'balance', 'bank', 'username', 'profile_color', 'embed_image', 'premium',
                         'message_streak', 'site_theme', 'site_accent_color', 'linked_roblox_account', 'crew_id', 'vouches',
                         'scammer_reports', 'reports', 'tickets', 'invited_by', 'invites',
                         'fake_invites'}
        if not all(key in valid_columns for key in kwargs.keys()):
            print(f"Invalid column name in update request for User ID {user_id}")
            return False

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
        return True
    except Exception as e:
        print(f"Error updating user ID {user_id}: {e}")
        await db.rollback()
        return False

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
        await add_user(user_id)
        insert_params = (code, amount, user_id)
        await db.execute(insert_query, insert_params)
        await db.commit()
        return code
    except Exception as e:
        print(f"Error creating code: {e}")
        await db.rollback()
        return None
    
async def get_total_members(db: aiosqlite.Connection):
    try:
        query = """
            SELECT COUNT(*)
            FROM membercount
        """
        async with db.execute(query) as cursor:
            result = await cursor.fetchone()
            return result[0]
    except Exception as e:
        print(f"Error fetching total members: {e}")
        return None


async def get_daily_members(db: aiosqlite.Connection):
    try:
        query = """
            SELECT COUNT(*)
            FROM membercount
            WHERE joined_at >= datetime('now', '-1 day')
        """
        async with db.execute(query) as cursor:
            result = await cursor.fetchone()
            return result[0]
    except Exception as e:
        print(f"Error fetching daily members: {e}")
        return None
    
async def get_bal_leaderboard(db: aiosqlite.Connection, type: str):
    try:
        if type == "total":
            # Calculate the total money by summing balance and bank for each user
            query = """
                SELECT id, (balance + bank) AS total
                FROM users
                ORDER BY total DESC
                LIMIT 100
            """
        elif type in ['balance', 'bank']:
            # Query based on the specified type (balance or bank)
            query = f"""
                SELECT id, {type}
                FROM users
                ORDER BY {type} DESC
                LIMIT 100
            """
        else:
            return None
        
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
        
        # Convert the rows to a list of dictionaries
        bal_leaderboard = []
        for row in rows:
            bal_leaderboard.append({
                'id': row[0],
                'amount': row[1],
            })
        
        return bal_leaderboard
    
    except Exception as e:
        print(f"Error fetching balance leaderboard: {e}")
        return None

async def get_top_messagers(db: aiosqlite.Connection):
    try:
        query = """
            SELECT id, username, messages
            FROM users
            ORDER BY messages DESC
            LIMIT 10000000
        """
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
        
        # Convert the rows to a list of dictionaries
        top_messagers = []
        for row in rows:
            top_messagers.append({
                'id': row[0],
                'roblox_username': row[1],
                'messages': row[2]
            })
        
        return top_messagers
    
    except Exception as e:
        print(f"Error fetching top messagers: {e}")
        return None