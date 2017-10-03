import math

from collections import defaultdict
from enum import Enum

from discord.ext import commands


class Gains(Enum):
    message = 10
    attachment = 5


def exp_needed(level):
    return 50 + round(5 * (level ** 2) - (5 * level))


def total_exp(level):
    i = 0
    for l in range(1, level - 1):
        i += exp_needed(l)
    return i


class Level:
    """A cog for checking activity in the form of experience"""

    def __init__(self, bot):
        self.bot = bot
        self.data = defaultdict(lambda: [1, 0])
        self.ch = None

    async def on_ready(self):
        self.ch = self.bot.get_channel(344104210406834176)

    async def on_message(self, msg):
        if msg.author == self.bot.user:
            return
        if msg.guild.id != 320567296726663178:
            return
        l, x = self.data[msg.author.id]
        x += Gains.message.value
        needed = exp_needed(l)
        if x >= needed:
            l += 1
            x -= needed
            await self.ch.send(f'{msg.author} leveled up to {l}, new xp: {x}/{exp_needed(l)}')
        self.data[msg.author.id] = l, x

    @commands.command()
    async def testxp(self, ctx, max: int, jump: int):
        output = ''
        for i in range(1, max, jump):
            output += f'Lv {i} - {exp_needed(i)}xp needed for lv{i+1}\n'
        await ctx.send(output)


def setup(bot):
    bot.add_cog(Level(bot))
