import asyncio
import datetime
import random

import discord
from discord.ext import commands


def custom_format(td):
    minutes, seconds = divmod(td.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return '{:d}:{:02d}'.format(hours, minutes)


class Raffle:

    def __init__(self, bot):
        self.bot = bot
        self.profiles = bot.get_cog("Profiles")
        self.raffle_channel = None
        self.raffles = []
        self.bg_task = bot.loop.create_task(self.raffle_interval())

    def __unload(self):
        self.bg_task.cancel()

    async def raffle_interval(self):
        await self.bot.wait_until_ready()
        # Load the channel and raffles from redis
        self.raffle_channel = self.bot.get_channel(467614160251912193)
        self.raffles = await self.bot.redis.keys('raffle:*', encoding='utf8')
        try:
            while not self.bot.is_closed():
                self.raffles = await self.bot.redis.keys('raffle:*', encoding='utf8')
                for key in self.raffles:
                    message_id = int(key.split(':')[1])
                    await self.update_raffle(message_id)
                    await asyncio.sleep(5)
                await asyncio.sleep(60)
        except Exception as e:
            print(e)

    async def update_raffle(self, message_id):
        message = await self.raffle_channel.get_message(message_id)
        end = await self.bot.redis.hget(f'raffle:{message_id}', 'end', encoding='utf8')
        end = datetime.datetime.utcfromtimestamp(int(end))

        if datetime.datetime.utcnow() >= end:
            entries = await self.bot.redis.lrange(f'raffle_entries:{message_id}', 0, -1, encoding='utf8') or ['???']
            winner = random.choice(entries)
            await message.edit(embed=await self.generate_end_embed(message_id, winner))
            await self.bot.redis.delete(f'raffle:{message_id}')
        else:
            await message.edit(embed=await self.generate_embed(message_id))

    @commands.has_role('Staff')
    @commands.command()
    async def createraffle(self, ctx, cost: int, hours: int, *, reward):
        message = await self.raffle_channel.send('setting up raffle..')
        await message.add_reaction('💎')

        raffle_id = await self.bot.redis.incr('rafflecount')
        endtime = datetime.datetime.utcnow() + datetime.timedelta(hours=hours)
        await self.bot.redis.hmset(f'raffle:{message.id}', 'raffle_id', raffle_id, 'cost', cost, 'reward', reward,
                                   'end', round((endtime - datetime.datetime(1970, 1, 1)).total_seconds()))

        await message.edit(content=None, embed=await self.generate_embed(message.id))
        self.raffles = await self.bot.redis.keys('raffle:*', encoding='utf8')

    @commands.has_role('Staff')
    @commands.command()
    async def clearraffles(self, ctx):
        await ctx.redis.delete(*await self.bot.redis.keys('raffle:*'))

    async def generate_embed(self, message_id):
        # fetch raffle info
        raffle_id, reward, cost, end = await self.bot.redis.hmget(f'raffle:{message_id}', 'raffle_id', 'reward', 'cost',
                                                                  'end', encoding='utf8')
        num_entries = await self.bot.redis.llen(f'raffle_entries:{message_id}')
        embed = discord.Embed(title=f"Raffle #{raffle_id} | Enter by reacting with 💎")
        embed.colour = 0x33cccc
        embed.add_field(name='Prize', value=str(reward or '?'))
        embed.add_field(name='Entry cost', value=str(cost or '?')+'g')
        embed.add_field(name='Entries', value=num_entries)
        # embed.add_field(name='Latest entries', value=f"", inline=False)
        embed.timestamp = datetime.datetime.utcfromtimestamp(float(end))
        embed.set_footer(text=f'⏰ Ends in {custom_format(datetime.datetime.utcfromtimestamp(float(end))-datetime.datetime.utcnow())} at')
        return embed

    async def generate_end_embed(self, message_id, winner_id):
        # fetch raffle info
        raffle_id, reward, cost, end = await self.bot.redis.hmget(f'raffle:{message_id}', 'raffle_id', 'reward', 'cost',
                                                                  'end', encoding='utf8')
        num_entries = await self.bot.redis.llen(f'raffle_entries:{message_id}')
        embed = discord.Embed(title=f"Raffle #{raffle_id}")
        embed.colour = 0xf25e9d
        embed.add_field(name='Prize', value=str(reward or '?'))
        embed.add_field(name='Entry cost', value=str(cost or '?')+'g')
        embed.add_field(name='Entries', value=num_entries)
        embed.add_field(name='Winner', value=f"<@{winner_id}>", inline=False)
        embed.timestamp = datetime.datetime.utcfromtimestamp(float(end))
        embed.set_footer(text=f'⏰ Ended')
        return embed

    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        if payload.channel_id != 467614160251912193:
            return
        if str(payload.emoji) != '💎':
            return

        # Get the entry cost, and also if a raffle exists in the first place
        cost, prize = await self.bot.redis.hmget(f'raffle:{payload.message_id}', 'cost', 'reward', encoding='utf8')
        if cost is None:
            return
        cost = int(cost)

        user = self.bot.get_user(payload.user_id)

        # Check if the user already entered
        if str(payload.user_id) in await self.bot.redis.lrange(f'raffle_entries:{payload.message_id}', 0, -1, encoding='utf8'):
            return await user.send("You already entered that raffle.")

        async with self.profiles.get_lock(payload.user_id):
            # Check if the user has enough gold
            profile = await self.profiles.get_profile(payload.user_id, ('coins',))
            if profile.coins < int(cost):
                return await user.send(f"Sorry, it costs {cost}g to enter for `{prize}`. You only have {profile.coins}g.")
            profile.coins -= int(cost)
            await profile.save(self.bot.db)

        await self.bot.redis.rpush(f'raffle_entries:{payload.message_id}', payload.user_id)
        await self.update_raffle(payload.message_id)
        await user.send(f"Thanks! You've entered the `{prize}` raffle for {cost}g.")


def setup(bot):
    bot.add_cog(Raffle(bot))
