import aiomysql


class DB:
    def __init__(self, host, username, password, db, loop):
        self.host = host
        self.username = username
        self.password = password
        self.db = db
        self.loop = loop
        self.pool = None

    async def connect(self):
        try:
            self.pool = await aiomysql.create_pool(host=self.host, port=3306,
                                                   user=self.username, password=self.password,
                                                   db=self.db, loop=self.loop)
        except:
            print("Couldn't connect to database.")

    async def execute(self, qry):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(qry)

    async def fetch(self, qry):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(qry)
                r = await cur.fetchall()
                return r

    async def fetchone(self, qry):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(qry)
                r = await cur.fetchone()
                return r

