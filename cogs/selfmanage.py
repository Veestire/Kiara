import discord
from discord.ext import commands


def get_color_role(member):
    for role in member.roles:
        if role.color == member.color:
            return role

class Selfmanage:
    """A cog for managing yourself"""

    def __init__(self, bot):
        self.bot = bot

    async def intro(self, ctx):
        await self.ask_question(ctx.author, 'How are you?')
        await ctx.send('okii')

    async def ask_question(self, user, question):
        await user.send(question)

        def check(m):
            return m.content == 'hello' and m.channel == user

        msg = await self.bot.wait_for('message', check=check)
        print(msg)


def setup(bot):
    bot.add_cog(Selfmanage(bot))
