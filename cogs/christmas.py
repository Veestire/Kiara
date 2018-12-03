import asyncio
import datetime
import random
import sys

import discord
from discord.ext import commands

import logging

log = logging.getLogger(__name__)


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
            log.error(e)

    async def drop_present(self, channel=None):
        ch = self.bot.get_channel(channel or 215424443005009920)

        emb = discord.Embed(color=discord.Color(0x09c500))
        emb.add_field(name='<:pr:514142499397173248> A big present has fallen from a sleigh high above.',
                      value="Claim your share before Santa comes down to take it back!\nType `claim`!")
        await ch.send(embed=emb)

        end_time = datetime.datetime.now() + datetime.timedelta(seconds=random.randint(5, 20))

        claimed = []

        messages = []

        for i in range(10):
            try:
                msg = await self.bot.wait_for('message', check=lambda m: m.author != self.bot.user and
                                                                         'claim' in m.content.lower() and
                                                                         m.channel.id == ch.id,
                                              timeout=(end_time - datetime.datetime.now()).total_seconds())
                messages += [msg]
                if msg.author.id in claimed:
                    continue
                claimed += [msg.author.id]
                await msg.add_reaction('👍')
            except asyncio.TimeoutError:
                break

        await ch.delete_messages(messages)

        share = ' and '.join(', '.join([f'<@{uid}>' for uid in claimed]).rsplit(', ', 1))

        emb = discord.Embed(color=discord.Color(0x09c500))
        emb.add_field(name=f'<:pr:514142498415706123> The present has been reclaimed.', value=f'{share} took a share for themselves.')
        await ch.send(embed=emb)

        for user_id in claimed:
            try:
                user = self.bot.get_user(user_id)
                if not user:
                    continue
                rand = random.random()
                if rand < .75:  # Daily
                    async with self.profiles.get_lock(user_id):
                        profile = await self.profiles.get_profile(user_id, ('coins',))
                        amount = int(random.randint(1, 3) * (1 + .2 * (profile.level // 5)))

                        if rand < .25:  # Double daily
                            amount *= 2
                        profile.coins += amount
                        await profile.save(self.bot.db)
                    await msg.author.send(f"Your share contained {amount} gold!")
                elif rand < .85:  # 50-100 gold
                    async with self.profiles.get_lock(user_id):
                        profile = await self.profiles.get_profile(user_id, ('coins',))
                        amount = random.randint(25, 50)
                        profile.coins += amount
                        await profile.save(self.bot.db)
                    await msg.author.send(f"Your share contained {amount} gold!")
                else:  # Random christmas color role
                    role_id, name = random.choice([(515821706535895050, 'Festive Fir'), (515822501037867009, 'Snowglobe'),
                                                  (515071275408949280, 'Christmas Spirit')])
                    owned = [r[0] for r in await self.bot.db.fetch(f'SELECT color FROM colors WHERE user_id={user_id}')]

                    if role_id in owned:
                        async with self.profiles.get_lock(user_id):
                            profile = await self.profiles.get_profile(user_id, ('coins',))
                            amount = int(random.randint(1, 3) * (1 + .2 * (profile.level // 5)))
                            profile.coins += amount
                            await profile.save(self.bot.db)
                        await msg.author.send(f"Your share contained {amount} gold!")
                    else:
                        await self.bot.db.execute(f'INSERT INTO colors (user_id, color) VALUES ({user_id}, {role_id})')
                        await msg.author.send(f"Your share contained the '{name}' role!\n"
                                              "It has been added to your color inventory.")
            except Exception as e:
                print(f'Fucksywucksy', file=sys.stderr)
                print(e, file=sys.stderr)

    @commands.command(hidden=True)
    @commands.has_role('Staff')
    async def droppresent(self, ctx, channel: int =None):
        await self.drop_present(channel)

def setup(bot):
    bot.add_cog(Christmas(bot))
