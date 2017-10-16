import datetime
import json
import random

import asyncio
import discord
from discord.ext import commands


def custom_format(td):
    minutes, seconds = divmod(td.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return '{:d}:{:02d}:{:02d}'.format(hours, minutes, seconds)


def can_change():
    async def predicate(ctx):
        return ctx.author.id in [73389450113069056, 211238461682876416]
    return commands.check(predicate)

def event_channel():
    async def predicate(ctx):
        return ctx.channel.id == 358962517290254356
    return commands.check(predicate)


class Halloween:
    """Commands for the halloween event~"""

    def __init__(self, bot):
        self.bot = bot
        self.conf = {}
        with open('trickortreat.json') as file:
            self.conf = json.load(file)


    @commands.group(aliases=['tot'])
    @event_channel()
    async def trickortreat(self, ctx):
        if ctx.invoked_subcommand:
            return
        cooldown = datetime.timedelta(hours=self.conf['cooldown'])
        r = await self.bot.db.fetchone(f'SELECT `timestamp` FROM cooldowns WHERE user_id={ctx.author.id}')
        if not r:
            await self.bot.db.execute(f'INSERT INTO cooldowns VALUES ({ctx.author.id}, "{ctx.message.created_at}")')
        else:
            d = abs(ctx.message.created_at - r[0])
            if d < cooldown:
                await ctx.send(f"You've recently entered the raffle, try again in {custom_format(cooldown-d)}")
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
        won = random.uniform(0, 100) < self.conf['chance']
        if won:
            emb.add_field(name='🎃 Trick Or Treat~', value=f'**{ctx.author.mention} pulled out... a small treasure chest!** 🌟')
            await self.dm_owner(ctx.author)
        else:
            emb.add_field(name='🎃 Trick Or Treat~', value=f'*{ctx.author.mention} {random.choice(responses)}*')
        await ctx.send(embed=emb)

    @trickortreat.command()
    @can_change()
    async def chance(self, ctx, *, value: float = None):
        if value:
            self.conf['chance'] = value
            with open('trickortreat.json', 'w') as file:
                json.dump(self.conf, file)
            await ctx.send(f"Set the chance to `{value}%`!")
        else:
            await ctx.send(self.conf['chance'])

    @trickortreat.command()
    @can_change()
    async def prize(self, ctx, *, value=None):
        if value:
            self.conf['prize'] = value
            with open('trickortreat.json', 'w') as file:
                json.dump(self.conf, file)
            await ctx.send(f"Set the prize to `{value}`!")
        else:
            await ctx.send(self.conf['prize'])

    @trickortreat.command()
    @can_change()
    async def cooldown(self, ctx, *, value: float = None):
        if value:
            self.conf['cooldown'] = value
            with open('trickortreat.json', 'w') as file:
                json.dump(self.conf, file)
            await ctx.send(f"Set the cooldown to `{value}` hours!")
        else:
            await ctx.send(self.conf['cooldown'])

    @commands.command()
    async def raffleinfo(self, ctx):
        emb = discord.Embed(color=discord.Color(0xf18f26), title='Raffle info')
        emb.add_field(name='Current prize', value=f"{self.conf['prize']}", inline=False)
        emb.add_field(name='Win chance', value=f"{self.conf['chance']:.3g}%")
        emb.add_field(name='Cooldown', value=f"{self.conf['cooldown']:.3g} hours")
        await ctx.send(embed=emb)

    async def dm_owner(self, winner):
        owner = self.bot.get_user(73389450113069056)
        emb = discord.Embed(color=discord.Color(0xf18f26), title='Raffle info')
        emb.add_field(name='Current prize', value=f"{self.conf['prize']}", inline=False)
        emb.add_field(name='Win chance', value=f"{self.conf['chance']:.3g}%")
        emb.add_field(name='Cooldown', value=f"{self.conf['cooldown']:.3g} hours")
        await owner.send(f"Hey master! Someone won the raffle!\nUser: {winner}\nAnd here's the info <3", embed=emb)



def setup(bot):
    bot.add_cog(Halloween(bot))
