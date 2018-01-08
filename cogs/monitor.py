import discord
from discord.ext import commands


class MemberID(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                return int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(f"{argument} is not a valid member or member ID.") from None
        else:
            return m.id


class Monitor:

    def __init__(self, bot):
        self.bot = bot
        self.logged_users = []

    @commands.command()
    @commands.has_any_role('Staff')
    async def monitor(self, ctx, member: MemberID):

        self.logged_users += [member]
        await ctx.send('')

    @commands.command()
    @commands.has_any_role('Staff')
    async def unmonitor(self, ctx, member: MemberID):
        self.logged_users += [member]

    async def on_member_join(self, member):
        if member.id in self.logged_users:


def setup(bot):
    bot.add_cog(Monitor(bot))
