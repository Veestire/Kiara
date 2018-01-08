import discord
from discord.ext import commands

MONITOR_CHANNEL = 399852942213251083

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

    @commands.group()
    @commands.has_any_role('Staff')
    async def monitor(self, ctx, member: MemberID):
        if ctx.invoked_subcommand is not None:
            return
        self.logged_users += [member]
        member = await self.bot.get_user_info(member)
        await ctx.send(f'Now monitoring {member}.')

    @monitor.command(name="list")
    @commands.has_any_role('Staff')
    async def monitor_list(self, ctx):
        if self.logged_users:
            await ctx.send('Users currently getting logged:\n'+'\n'.join([self.bot.get_user(u) or u for u in self.logged_users]))
        else:
            await ctx.send('No users are getting logged atm.')

    @commands.command()
    @commands.has_any_role('Staff')
    async def unmonitor(self, ctx, member: MemberID):
        self.logged_users.remove(member)
        member = await self.bot.get_user_info(member)
        await ctx.send(f'No longer monitoring {member}.')

    async def on_member_join(self, member):
        if member.id in self.logged_users:
            ch = self.bot.get_channel(MONITOR_CHANNEL)
            await ch.send(f'{member.mention} joined the server.')

    async def on_member_remove(self, member):
        if member.id in self.logged_users:
            ch = self.bot.get_channel(MONITOR_CHANNEL)
            await ch.send(f'{member.mention} is no longer on the server.')

    async def on_message_delete(self, message):
        if message.author.id in self.logged_users:
            ch = self.bot.get_channel(MONITOR_CHANNEL)
            await ch.send(f'Message deleted from {message.author.mention}')
            await ch.send(f'```\n{message.content}```')
            if message.attachments:
                await ch.send('\n'.join([x.url for x in message.attachments]))


def setup(bot):
    bot.add_cog(Monitor(bot))
