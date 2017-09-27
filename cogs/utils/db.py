import aiomysql


class DB:
    def __init__(self, host, username, password, db, loop):
        self.host = host
        self.username = username
        self.password = password
        self.db = db
        self.loop = loop
        self.con = None
        self.cur = None

    async def connect(self):
        try:
            self.con = await aiomysql.connect(host=self.host, port=3306, user=self.username, password=self.password,
                                              db=self.db, loop=self.loop)
            self.cur = await self.con.cursor(aiomysql.DictCursor)
        except:
            print("Couldn't connect to database.")

    async def execute(self, qry):
        await self.cur.execute(qry)

    async def fetch(self, qry):
        await self.cur.execute(qry)
        r = await self.cur.fetchall()
        return r

    async def fetchone(self, qry):
        await self.cur.execute(qry)
        r = await self.cur.fetchone()
        return r

