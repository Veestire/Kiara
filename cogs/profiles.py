import asyncio
import datetime
import random
from .utils import time
from discord.ext import commands
import discord

from async_generator import asynccontextmanager

EXCLUDED_CHANNELS = [269910005837332480, 451729018199212032]


def exp_needed(level):
    return level * 250


def exp_total(level):
    return sum([exp_needed(x) for x in range(level + 1)])


def needs_profile(keys=None):
    async def predicate(ctx):
        if ctx.guild is None:
            return False

        if ctx.invoked_with.lower() == 'help':
            return True

        cog = ctx.bot.get_cog('Profiles')
        async with ctx.typing():
            ctx.profile = await cog.get_profile(ctx.author.id, keys)

        return True

    return commands.check(predicate)


def levelup_gold(lvl):
    if lvl <= 5:
        amount = random.randint(1, 10)
    elif lvl <= 10:
        amount = random.randint(5, 10)
    elif lvl <= 20:
        amount = random.randint(5, 15)
    elif lvl <= 30:
        amount = random.randint(10, 20)
    elif lvl <= 40:
        amount = random.randint(15, 20)
    elif lvl <= 50:
        amount = random.randint(20, 30)
    else:
        amount = random.randint(25, 35)
    return amount


class Profile:
    __slots__ = ('user_id', 'level', 'experience', 'fame', 'coins')

    def __init__(self, uid, **kwargs):
        self.user_id = uid
        self.level = kwargs.get('level', 1)
        self.experience = kwargs.get('experience', 0)
        self.coins = kwargs.get('coins', 0)

    async def save(self, db):
        s = ','.join([f'{s}={getattr(self,s,None)}' for s in self.__slots__[1:] if getattr(self, s, None) is not None])
        await db.execute(f"UPDATE profiles SET {s} WHERE user_id={self.user_id}")

    async def has_item(self, name=None):
        pass


class Profiles:
    """Stuff for profiles"""

    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        self._locks = dict()

        self.exp_rate = 1
        self.gold_rate = 1

    @asynccontextmanager
    async def transaction(self, user_id):
        async with self.get_lock(user_id):
            profile = await self.get_profile(user_id)
            yield profile
            await profile.save(self.bot.db)

    def get_lock(self, name):
        lock = self._locks.get(name)
        if not lock:
            lock = asyncio.Lock(loop=self.bot.loop)
            self._locks[name] = lock
        return lock

    async def get_profile(self, uid, keys=None):
        profile = await self.bot.db.fetchdict(f'SELECT * FROM profiles WHERE user_id={uid}')
        if not profile:
            await self.bot.db.execute(f'INSERT INTO profiles (user_id) VALUES ("{uid}")')
            return Profile(uid, level=0, experience=0, coins=0)
        return Profile(uid, **profile)

    async def on_message(self, msg):
        if not msg.guild:
            return
        if msg.channel.id in EXCLUDED_CHANNELS:
            return
        if msg.author.bot:
            return
        async with self.get_lock(msg.author.id):
            profile = await self.get_profile(msg.author.id, ('level', 'experience', 'coins'))

            d = abs(msg.created_at - self.cooldowns.get(profile.user_id, datetime.datetime(2000, 1, 1)))
            if d < datetime.timedelta(seconds=5):
                return

            profile.experience += 10*self.exp_rate

            # Bonus for images
            if msg.attachments:
                profile.experience += 30*self.exp_rate
            else:
                self.cooldowns[profile.user_id] = msg.created_at

            needed = exp_needed(profile.level)

            # Terrible temporary levelup
            if profile.experience >= needed:
                profile.level += 1
                profile.experience -= needed
                profile.coins += levelup_gold(profile.level)*self.gold_rate

                # Temporary faithful role, the whole role idea will change in the future.
                if profile.level == 3:
                    await msg.author.add_roles(discord.utils.get(msg.guild.roles, id=457213160504426496))

                if profile.level % 5 == 0:
                    role = discord.utils.get(msg.guild.roles, name=str(profile.level))
                    if role:
                        await msg.author.add_roles(role, reason=f"Reached level {profile.level}")
                        rem = discord.utils.get(msg.guild.roles, name=str(max(profile.level - 5, 1)))
                        await msg.author.remove_roles(rem, reason=f"Reached level {profile.level}")

            await profile.save(self.bot.db)

    async def on_member_join(self, member):
        profile = await self.get_profile(member.id, ('level',))
        role = discord.utils.get(member.guild.roles, name=str(profile.level // 5 * 5))
        if role:
            await member.add_roles(role, reason=f"Re-joined the server at level {profile.level}")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def givegold(self, ctx, member: discord.Member, gold: int):
        async with self.get_lock(ctx.author.id):
            profile = await self.get_profile(member.id, ['coins'])
            profile.coins += gold
            await profile.save(self.bot.db)
            await ctx.send(f"{member} now has {profile.coins} gold")

    @commands.command(hidden=True, aliases=['givecolour'])
    @commands.has_permissions(administrator=True)
    async def givecolor(self, ctx, member: discord.Member, *, color):
        role = discord.utils.find(lambda x: color.lower() in x.name.lower(), ctx.guild.roles)
        if not role:
            return await ctx.send("Unknown color/role")
        await self.bot.db.execute(f'INSERT INTO colors (user_id, color) VALUES ({member.id}, {role.id})')
        await ctx.send(f"Gave {member} the role <@&{role.id}>")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def takegold(self, ctx, member: discord.Member, gold: int):
        async with self.get_lock(ctx.author.id):
            profile = await self.get_profile(member.id, ['coins'])
            profile.coins -= gold
            await profile.save(self.bot.db)
            await ctx.send(f"{member} now has {profile.coins} gold")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def setlevel(self, ctx, member: discord.Member, level: int, xp: int = None):
        async with self.get_lock(ctx.author.id):
            profile = await self.get_profile(member.id, ['level'])
            profile.level = level
            if xp:
                profile.experience = xp
            await profile.save(self.bot.db)
            await ctx.send(f"{member} is now level {level}")

    @commands.command()
    async def profile(self, ctx):
        """Display your profile"""
        member = ctx.author
        e = discord.Embed(title=member.display_name)
        e.set_thumbnail(url=member.avatar_url_as(size=128))
        e.add_field(name=f'Created', value=time.time_ago(member.created_at), inline=True)
        if ctx.guild:
            if member.id == 73389450113069056:
                member.joined_at = ctx.guild.created_at
            e.add_field(name=f'Joined', value=time.time_ago(member.joined_at), inline=True)
            e.add_field(name=f'Nickname', value=member.nick or "None", inline=False)
            e.add_field(name=f'Roles', value=' '.join([role.mention for role in member.roles[:0:-1]]), inline=False)

            role = self.get_top_color(member.roles) if ctx.guild else None
            if role:
                e.colour = role.color
        econ = self.bot.get_cog('Economy')
        if econ:
            items = await econ.get_inventory(ctx.author.id)
            if items:
                items = [f'<:bs:{item["icon"]}>' for item in items]
                e.add_field(name="Inventory", value=' '.join(items))
        await ctx.send(embed=e)

    @commands.command(hidden=True)
    async def top(self, ctx, page: int = 1):
        """Display the wealthiest members on the server"""
        guild = self.bot.get_guild(215424443005009920)
        qry = f"""
            select `user_id`, `coins`, `rank` FROM
            (
            select t.*, @r := @r + 1 as `rank`
            from  profiles t,
            (select @r := 0) r
            order by `coins` desc
            ) as t
            limit %s, %s
            """
        r = await ctx.bot.db.fetch(qry, ((page - 1) * 10, 10))
        w = max(len(getattr(guild.get_member(user_id), 'display_name', 'user_left')) for user_id, coins, rank in r)
        output = '```\n' + '\n'.join([
            f"{int(rank):<3} - {getattr(guild.get_member(user_id),'display_name','user_left'):<{w}} - {coins:<7} coins"
            for user_id, coins, rank in r]) + '```'
        await ctx.send(output)

    @commands.command(hidden=True)
    async def rank(self, ctx, member: discord.Member = None):
        if not member:
            member = ctx.author
        qry = f"""
        select `level`, `experience`, `rank` FROM
        (
        select t.*, @r := @r + 1 as `rank`
        from  profiles t,
        (select @r := 0) r
        order by `level` desc, `experience` desc
        ) as t
        where `user_id`={member.id}
        """
        lvl, xp, rank = await ctx.bot.db.fetchone(qry)
        em = discord.Embed(title=f'**{member.display_name}**', color=0x77dd77,
                           description=f'**Rank {round(rank)} - Lv{lvl}** {xp}/{exp_needed(lvl)}xp')
        await ctx.send(embed=em)

    @commands.command(hidden=True, aliases=['leaderboards', 'ranks', 'rankings'])
    async def leaderboard(self, ctx, page: int = 1):
        """Display the server leaderboard"""
        guild = self.bot.get_guild(215424443005009920)
        qry = f"""
        select `user_id`, `level`, `experience`, `rank` FROM
        (
        select t.*, @r := @r + 1 as `rank`
        from  profiles t,
        (select @r := 0) r
        order by `level` desc, `experience` desc
        ) as t
        limit %s, %s
        """
        r = await ctx.bot.db.fetch(qry, ((page - 1) * 10, 10))
        w = max(len(getattr(guild.get_member(user_id), 'display_name', 'user_left')) for user_id, lvl, xp, rank in r)
        output = '```\n' + '\n'.join([
                                         f"{int(rank):<3} - {getattr(guild.get_member(user_id),'display_name','user_left'):<{w}} - Lv{lvl:<4} {xp:<5} / {exp_needed(lvl):>5}xp"
                                         for user_id, lvl, xp, rank in r]) + '```'
        await ctx.send(output)

    @commands.command(aliases=['experience'])
    async def xp(self, ctx, *, member: discord.Member = None):
        """Check your xp"""
        if not member:
            member = ctx.author
        p = await self.get_profile(member.id, ('level', 'experience'))
        em = discord.Embed(title=f'{member.display_name}')
        em.add_field(name="Level", value=f'**{p.level}**')
        em.add_field(name="Exp", value=f'{p.experience}/{exp_needed(p.level)}xp')
        em.set_thumbnail(url=member.avatar_url_as(size=64))

        role = self.get_top_color(member.roles)
        if role:
            em.colour = role.color

        await ctx.send(embed=em)

    def get_top_color(self, roles):
        excluded = ['Muted', 'Guardian Angel']
        for role in roles[::-1]:
            if role.color != discord.Colour.default() and role.name not in excluded:
                return role
        return None

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def exprate(self, ctx, rate: float = None):
        if rate:
            self.exp_rate = rate
        await ctx.send(f"Exp rate is now x{self.exp_rate}")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def goldrate(self, ctx, rate: float = None):
        if rate:
            self.gold_rate = rate
        await ctx.send(f"Gold rate is now x{self.gold_rate}")

def setup(bot):
    bot.add_cog(Profiles(bot))
