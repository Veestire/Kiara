import random

import asyncio
import discord
from discord.ext import commands


class Gala:
    """Gala test commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def trickortreat(self, ctx):
        r = await self.bot.db.fetchone(f'SELECT `timestamp` FROM cooldowns WHERE user_id={ctx.author.id}')
        if not r:
            await self.bot.db.execute(f'INSERT INTO cooldowns VALUES ({ctx.author.id}, "{ctx.message.created_at}")')
        else:
            print(r)
        return
        # d = abs(ctx.message.created_at - timestamp)
        msg = f"You've recently entered the raffle, try again in {left}"
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
    bot.add_cog(Gala(bot))
