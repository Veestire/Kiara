import random
from collections import OrderedDict
from enum import Enum

import discord
from discord.ext import commands

base_colors = [
    ("Red", 424579184216506368, 30),
    ("Yellow", 424579315066208276, 30),
    ("Green", 424579385983762432, 30),
    ("Orange", 424579446578872332, 30),
    ("Cyan", 424579523363733507, 30),
    ("Blue", 424579641802752000, 30),
    ("Purple", 424579707573633024, 30),
    ("Pink", 424579770240466951, 30),
    ("Charcoal", 424579833994149888, 30),
]

extra_colors = [
    ("Cold Winter Breeze", 403584549847564304,45),
    ("Brilliant Bronze", 399125560661377025,45),
    ("Twilight", 360765369180225556,45),
    ("Journey", 360792645389516811,45),
    ("Love Is In The Air", 360765505788968961,60),
    ("The Light Of A Soul That Will Never Fade", 360792991968788480,60),
    ("Burning Passion", 360766053678055424,60),
    ("Seductive Embrace", 383816911072395269,60),
    ("A Story Untold", 360785400798904331,60),
    ("Reflections Of A Day Long Gone", 360791701025062913,60),
    ("A Darkness Only Seen Within", 360788545759084554,100),
    ("Spring Petal Dancing In The Mist", 403591076532846596,100),
    ("Lost in the Orchid Garden", 403583624558936065,100),
    ("Look Into The Stars", 369825912813780993,100),
    ("Walkin' on a Sunset", 383817936898490378,100),
]


class Shop:
    __slots__ = ('name', 'items')

    def __init__(self, name):
        self.name = name
        self.items = []

    def add(self, item):
        self.items += [item]

    def get(self, item):
        return discord.utils.get(self.items, name=item)


class ItemType(Enum):
    GENERIC = 0
    ROLE = 1


class Item:
    __slots__ = ('name', 'type', 'cost', 'data')

    def __init__(self, name, type, cost, data):
        self.name = name
        self.type = type
        self.cost = cost
        self.data = data

    def get_role(self):
        return 0


class Economy:

    def __init__(self, bot):
        self.bot = bot
        self.profiles = bot.get_cog("Profiles")
        self.shops = [
            Shop('Role shop'),
            Shop('Premium shop')
        ]
        for name, data, cost in base_colors:
            self.shops[0].add(Item(name, ItemType.ROLE, cost=cost, data=data))
        for name, data, cost in extra_colors:
            self.shops[1].add(Item(name, ItemType.ROLE, cost=cost, data=data))

    @commands.cooldown(1, 86400, commands.BucketType.user)
    @commands.command(aliases=['daily'])
    async def dailies(self, ctx):
        amount = random.randint(1, 5)
        profile = await self.profiles.get_profile(ctx.author.id, ('coins',))
        profile.coins += amount
        await profile.save(self.bot.db)
        await ctx.send(f"You got {amount} gold as daily reward.")

    @dailies.error
    async def dailies_error(self, ctx, error):
        m, s = divmod(error.retry_after, 60)
        h, m = divmod(m, 60)
        msg = "You can use this command once per 24 hours.\nTry again in "
        if h:
            msg += f"{h} hour(s)"
        elif m:
            msg += f"{m} minutes and {s} seconds"
        else:
            msg += f"{s} seconds"
        await ctx.send(msg)

    @commands.command(hidden=True)
    async def shop(self, ctx, *, name=None):
        em = discord.Embed(title="Color shop~", description="You can buy your colors here. To buy, type `~buy [color]`")
        for shop in self.shops:
            for item in shop.items:
                em.add_field(name=f'{item.name}', value=f"{item.cost}g")
        em.set_footer(text=f"You have x gold")
        await ctx.send(embed=em)

    @commands.command(hidden=True)
    async def buy(self, ctx, *, item):

        pass

def setup(bot):
    bot.add_cog(Economy(bot))
