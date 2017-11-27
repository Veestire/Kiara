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


class Christmas:
    """Commands for the christmas event~"""

    def __init__(self, bot):
        self.bot = bot
        self.conf = {}
        with open('raffle.json') as file:
            self.conf = json.load(file)

    @commands.group()
    @can_change()
    async def raffle(self, ctx):
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
        pre = [
            'unwrapped their gift, and found...',
            'put their hand inside the stocking, and pulled out...',
            'opened a cardboard box, and pulled out...',
            'got something thrown at them, it was...',
            'got a present from a passerby, it contained...',
            'found found a suspicious looking box on the floor, it contained...'
        ]
        lose = [
            'Coal… Lots of coal.',
            'Soggy biscuits, did Santa leave them?',
            f'A bag of chocolates!... Wait, they expired in {random.randrange(1900,2016)}.',
            'A deep inner sadness.',
            'A pair of socks.',
            "A pair of kneesocks, but they don't fit.",
            f'{random.randrange(10,100)} used matches.',
            'Expired milk.'
        ]
        emb = discord.Embed(color=discord.Color(0xfdd888))
        roll = random.uniform(0, 100)
        won = roll <= self.conf['chance']
        if won:
            emb.add_field(name='🎁 Merry Christmas~', value=f'*{ctx.author.mention} {random.choice(pre)}*\n'
                                                            f'**A gift from santa, just for them!** 🌟')
            # await self.dm_owner(ctx.author)
        else:
            emb.add_field(name='🎁 Merry Christmas~', value=f'*{ctx.author.mention} {random.choice(pre)}\n'
                                                            f'{random.choice(lose)}*')
        emb.set_footer(text=f'Rolled {roll:.2f} / 100 (Roll under {self.conf["chance"]} to win)',
                       icon_url='https://cdn.discordapp.com/attachments/231008480079642625/369344924556197889/1adc9faf91526bb7a2c1d0b7b3516cae.png')
        await ctx.send(embed=emb)

    @raffle.command()
    @commands.has_permissions(administrator=True)
    async def chance(self, ctx, *, value: float = None):
        if value:
            self.conf['chance'] = value
            with open('raffle.json', 'w') as file:
                json.dump(self.conf, file)
            await ctx.send(f"Set the chance to `{value}%`!")
        else:
            await ctx.send(self.conf['chance'])

    @raffle.command()
    @commands.has_permissions(administrator=True)
    async def prize(self, ctx, *, value=None):
        if value:
            self.conf['prize'] = value
            with open('raffle.json', 'w') as file:
                json.dump(self.conf, file)
            await ctx.send(f"Set the prize to `{value}`!")
        else:
            await ctx.send(self.conf['prize'])

    @raffle.command()
    @commands.has_permissions(administrator=True)
    async def cooldown(self, ctx, *, value: float = None):
        if value:
            self.conf['cooldown'] = value
            with open('raffle.json', 'w') as file:
                json.dump(self.conf, file)
            await ctx.send(f"Set the cooldown to `{value}` hours!")
        else:
            await ctx.send(self.conf['cooldown'])

    @raffle.command()
    @commands.has_permissions(administrator=True)
    async def resetcooldowns(self, ctx):
        """Reset all user's raffle cooldowns"""
        await self.bot.db.execute(f'UPDATE cooldowns SET timestamp="2000-01-01 00:00:00" WHERE 1')
        await ctx.send('Cooldowns reset!')

    @commands.command()
    async def raffleinfo(self, ctx):
        emb = discord.Embed(color=discord.Color(0xfdd888), title='Raffle info')
        emb.add_field(name='Current prize', value=f"{self.conf['prize']}", inline=False)
        emb.add_field(name='Win chance', value=f"{self.conf['chance']:.3g}%")
        emb.add_field(name='Cooldown', value=f"{self.conf['cooldown']:.3g} hours")
        await ctx.send(embed=emb)

    async def dm_owner(self, winner):
        owner = self.bot.get_user(73389450113069056)
        emb = discord.Embed(color=discord.Color(0xfdd888), title='Raffle info')
        emb.add_field(name='Current prize', value=f"{self.conf['prize']}", inline=False)
        emb.add_field(name='Win chance', value=f"{self.conf['chance']:.3g}%")
        emb.add_field(name='Cooldown', value=f"{self.conf['cooldown']:.3g} hours")
        await owner.send(f"Hey master! Someone won the raffle!\nUser: {winner}\nAnd here's the info <3", embed=emb)



def setup(bot):
    bot.add_cog(Christmas(bot))
