from discord.ext import commands

class Manage:
    """Commands for managing Rub as user"""

    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.group(hidden=True, aliases=['set', 'mng'])
    async def manage(self, ctx):
        """Manage Rub"""
        if ctx.invoked_subcommand is None:
            raise commands.CommandInvokeError

    @manage.command(hidden=True, aliases=['user'])
    async def username(self, ctx, *, name):
        """Set Rub's username."""
        await self.bot.user.edit(username=name)

    @manage.command(hidden=True, aliases=['nick'])
    @commands.guild_only()
    async def nickname(self, ctx, *, name=None):
        """Set Rub's nickname."""
        await ctx.guild.me.edit(nick=name)

    @manage.command(hidden=True, aliases=['ava'])
    async def avatar(self, ctx, *, url=None):
        """Set Rub's avatar."""
        if url:
            async with self.bot.session.get(url) as resp:
                if resp.status == 200:
                    await self.bot.user.edit(avatar=await resp.read())
        else:
            if ctx.message.attachments:
                async with self.bot.session.get(ctx.message.attachments[0].url) as resp:
                    if resp.status == 200:
                        await self.bot.user.edit(avatar=await resp.read())
            else:
                await self.bot.user.edit(avatar=None)

def setup(bot):
    bot.add_cog(Manage(bot))
