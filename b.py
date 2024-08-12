import asyncio
import aiomysql

# Database connection parameters
config = {
    'user': 'u140785_gvrm4uzhcl',
    'password': '6+YN0S4@VM3V9FwNZl7yY1uH',
    'host': 'db-buf-05.sparkedhost.us',
    'port': 3306,
    'db': 's140785_database'
}

async def fetch_prefix():
    # Create a connection pool
    pool = await aiomysql.create_pool(**config)
    
    async with pool.acquire() as connection:
        async with connection.cursor() as cursor:
            # Execute the query to get the prefix
            query = "SELECT prefix FROM prefix LIMIT 1;"
            await cursor.execute(query)
            
            # Fetch the result
            result = await cursor.fetchone()
            if result:
                print(f"Prefix: {result[0]}")
            else:
                print("No prefix found.")
    
    # Close the pool
    pool.close()
    await pool.wait_closed()

# Run the async function
if __name__ == '__main__':
    asyncio.run(fetch_prefix())
