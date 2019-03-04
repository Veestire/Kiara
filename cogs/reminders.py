import asyncio
import datetime

import parsedatetime as pdt
from discord.ext import commands


def get_date(text):
    cal = pdt.Calendar()
    time, res = cal.parseDT(text, datetime.datetime.utcnow())
    return time if res else None

class Reminders(commands.Cog):
    """Tools for reminding"""
    def __init__(self, bot):
        self.bot = bot
        self.timers = bot.get_cog('Timers')

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.channel.id != 269910005837332480:
            return
        if msg.content.lower().startswith('remind '):
            reminder = msg.content[7:]
            if reminder.lower().startswith('me '):
                reminder = reminder[3:]
            if reminder.lower().startswith('to '):
                reminder = reminder[3:]

            time = get_date(reminder)
            if not time:
                await msg.channel.send("When?")
                msg = await self.bot.wait_for('message',
                                              check=lambda m: m.author == msg.author and m.channel == msg.channel)
                time = get_date(msg.content)
            if time:
                await self.timers.create_timer('reminder', time, [msg.author.id, msg.channel.id, reminder])
                await msg.channel.send(f'I\'ll remind you then!')
            else:
                await msg.channel.send(f"Idk when you want me to remind you")

    @commands.Cog.listener()
    async def on_reminder_event(self, author_id, destination_id, msg):
        author = self.bot.get_user(author_id)
        if author is None:
            return
        channel = self.bot.get_channel(destination_id)
        if channel is None:
            # Check if it's a DM channel
            author = self.bot.get_user(author_id)
            try:
                channel = await author.dm_channel()
            except:
                return

        await channel.send(f'{author.mention}\n{msg}')

def setup(bot):
    bot.add_cog(Reminders(bot))
