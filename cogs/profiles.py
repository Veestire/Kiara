import datetime
import random
from collections import defaultdict

import aiohttp
from discord.ext import commands
import discord

EXCLUDED_CHANNELS = [
]

def exp_needed(level):
    # return round(20 * level ** 1.05)
    return level*100


def exp_total(level):
    return sum([exp_needed(x) for x in range(level+1)])


def needs_profile(keys=None):
    async def predicate(ctx):
        if ctx.guild is None:
            return False

        cog = ctx.bot.get_cog('Profiles')
        async with ctx.typing():
            ctx.profile = await cog.get_profile(ctx.author.id, keys)

        return True
    return commands.check(predicate)


class PartialProfile:
    __slots__ = ('pid', 'level', 'experience', 'coins')

    def __init__(self, pid, **kwargs):
        self.pid = pid
        self.level = 1
        self.experience = 0
        self.coins = 200
        for k in kwargs:
            setattr(self, k, kwargs[k])

    async def save(self, db):
        s = ', '.join([f'{s}={getattr(self,s,None)}' for s in self.__slots__[1:] if getattr(self, s, None) is not None])
        await db.execute(f"UPDATE profiles SET {s} WHERE id={self.pid}")


class Profiles:
    """Stuff for profiles"""

    def __init__(self, bot):
        self.bot = bot
        # self.cooldowns = {}
        self.profiles = {}

    async def get_profile(self, u_id, keys=None):
        if u_id in self.profiles:
            p_id = self.profiles[u_id]
        else:
            p_id, = await self.bot.db.fetchone(f'SELECT id FROM profiles WHERE user_id={u_id}') or (None,)
            if not p_id:
                _, p_id = await self.bot.db.execute(f'INSERT INTO profiles (user_id) VALUES ({u_id})')
            self.profiles[u_id] = p_id
        if keys:
            s = ', '.join(keys)
            data = await self.bot.db.fetchone(f'SELECT {s} FROM profiles WHERE id={p_id}', assoc=True)
            return PartialProfile(p_id, **data)
        return PartialProfile(p_id)

    async def on_message(self, msg):
        if not msg.guild:
            return
        if msg.channel.id in EXCLUDED_CHANNELS:
            return
        if msg.author.bot:
            return
        profile = await self.get_profile(msg.author.id, ('level', 'experience', 'coins'))
        # d = abs(msg.created_at - self.cooldowns.get(profile.pid, datetime.datetime(2000, 1, 1)))
        # if d < datetime.timedelta(seconds=20):
        #     return
        profile.experience += 10
        if msg.attachments:
            profile.experience += 10
        profile.coins += 1
        needed = exp_needed(profile.level)
        if profile.experience >= needed:
            profile.level += 1
            profile.experience -= needed
        await profile.save(self.bot.db)
        # self.cooldowns[profile.pid] = msg.created_at

    @commands.command(hidden=True)
    @commands.has_role('Admin')
    async def setlevel(self, ctx, member: discord.Member, level: int, xp: int= None):
        ctx.profile = await self.get_profile(member.id, ['level'])
        ctx.profile.level = level
        if xp:
            ctx.profile.experience = xp
        await ctx.profile.save(self.bot.db)
        await ctx.send(f"{member} is now level {level}")

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
        em = discord.Embed(title=f'**{member}**',
                           description=f'**Rank {rank} - Lv{lvl}** {xp}/{exp_needed(lvl)}xp')
        await ctx.send(embed=em)

    @commands.command(hidden=True)
    async def leaderboard(self, ctx):
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
        limit 10
        """
        r = await ctx.bot.db.fetch(qry)
        output = '```\n'+'\n'.join([f"{rank} - {ctx.guild.get_member(user_id)}" for lxl, xp, rank in r])+'```'
        await ctx.send(output)

    @commands.command(hidden=True)
    async def xp(self, ctx, member: discord.Member = None):
        if not member:
            member = ctx.author
        p = await self.get_profile(member.id, ('level', 'experience'))
        em = discord.Embed(title=f'**{member}**',
                           description=f'**Lv{p.level}** {p.experience}/{exp_needed(p.level)}xp')
        await ctx.send(embed=em)

def setup(bot):
    bot.add_cog(Profiles(bot))
