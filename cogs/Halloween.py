import datetime
import random

import asyncio
import discord
from discord.ext import commands


class Halloween:
    """Commands for the halloween event~"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def trickortreat(self, ctx):
        r = await self.bot.db.fetchone(f'SELECT `timestamp` FROM cooldowns WHERE user_id={ctx.author.id}')
        if not r:
            await self.bot.db.execute(f'INSERT INTO cooldowns VALUES ({ctx.author.id}, "{ctx.message.created_at}")')
        else:
            d = abs(ctx.message.created_at - r[0])
            if d < datetime.timedelta(minutes=2):
                await ctx.send(f"You've recently entered the raffle, try again in {d}")
                return
            else:
                await self.bot.db.execute(
                    f'UPDATE cooldowns SET timestamp="{ctx.message.created_at}" WHERE user_id={ctx.author.id}')
        responses = [
            'pulled out... a dead spider! 🕷',
            'pulled out... an old candy bar 🍬',
            'pulled out... a dusty skull... 💀',
            'pulled out... a sheet with cut-out eyes 👻',
        ]
        emb = discord.Embed(color=discord.Color(0xf18f26))
        won = random.randrange(0, 100) < 25
        if won:
            emb.add_field(name='🎃 Trick Or Treat~', value=f'*{ctx.author.mention} pulled out... a small treasure chest!*')
        else:
            emb.add_field(name='🎃 Trick Or Treat~', value=f'*{ctx.author.mention} {random.choice(responses)}*')
        await ctx.send(embed=emb)


def setup(bot):
    bot.add_cog(Halloween(bot))
