import asyncio
import random

import discord
import itertools
from discord.ext import commands

class Christmas:
    """Merry christmas"""

    def __init__(self, bot):
        self.bot = bot
        self.profiles = self.bot.get_cog('Profiles')
        self.bg_task = bot.loop.create_task(self.drop_present_task())

    def __unload(self):
        self.bg_task.cancel()

    async def drop_present_task(self):
        await self.bot.wait_until_ready()
        try:
            while not self.bot.is_closed():
                if random.random() <= 0.03:
                    await self.drop_present()
                await asyncio.sleep(60)
        except Exception as e:
            print(e)

    async def drop_present(self, channel=None):
        ch = self.bot.get_channel(channel or 215424443005009920)

        emb = discord.Embed(color=discord.Color(0xfdd888))
        emb.add_field(name='<:pr:514142498415706123> A present magically appeared on the floor!',
                      value="Type `claim` to claim it!")
        await ch.send(embed=emb)

        msg = await self.bot.wait_for('message', check=lambda m: m.author != self.bot.user and 'claim' in m.content.lower())

        emb = discord.Embed(color=discord.Color(0xfdd888),
                            title=f'<:pr:514142499397173248> {msg.author.display_name} claimed the present!')
        await ch.send(embed=emb)

        rand = random.random()
        print(f"{msg.author} claimed present ({rand})")
        if rand < .75:  # Daily
            async with self.profiles.get_lock(msg.author.id):
                profile = await self.profiles.get_profile(msg.author.id, ('coins',))
                amount = int(random.randint(1, 5) * (1 + .2 * (profile.level // 5)))

                if rand < .25:  # Double daily
                    amount *= 2
                profile.coins += amount
                await profile.save(self.bot.db)
            await msg.author.send(f"Your present contained {amount} gold!")
        elif rand < .85:  # 50-100 gold
            async with self.profiles.get_lock(msg.author.id):
                profile = await self.profiles.get_profile(msg.author.id, ('coins',))
                amount = random.randint(50, 100)
                profile.coins += amount
                await profile.save(self.bot.db)
            await msg.author.send(f"Your present contained {amount} gold!")
        else:  # Random christmas color role
            role_id, name = random.choice([(515821706535895050, 'Festive Fir'), (515822501037867009, 'Snowglobe'),
                                          (515071275408949280, 'Christmas Spirit')])
            owned = [r[0] for r in await self.bot.db.fetch(f'SELECT color FROM colors WHERE user_id={msg.author.id}')]

            if role_id in owned:
                async with self.profiles.get_lock(msg.author.id):
                    profile = await self.profiles.get_profile(msg.author.id, ('coins',))
                    amount = int(random.randint(1, 5) * (1 + .2 * (profile.level // 5)))
                    profile.coins += amount
                    await profile.save(self.bot.db)
                await msg.author.send(f"Your present contained {amount} gold!")
            else:
                await self.bot.db.execute(f'INSERT INTO colors (user_id, color) VALUES ({msg.author.id}, {role_id})')
                await msg.author.send(f"Your present contained the '{name}' role!\n"
                                      "It has been added to your color inventory.")

    @commands.command(hidden=True)
    @commands.has_role('Staff')
    async def droppresent(self, ctx, channel: int =None):
        await self.drop_present(channel)

def setup(bot):
    bot.add_cog(Christmas(bot))
