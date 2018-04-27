import discord
from discord.ext import commands


class Helpful:

    def __init__(self, bot):
        self.bot = bot

    @commands.has_any_role('Staff')
    @commands.command(hidden=True)
    async def avatar(self, ctx, user: discord.Member = None):
        """Show someones avatar."""
        if not user:
            user = ctx.author
        await ctx.send(embed=discord.Embed().set_image(url=user.avatar_url).set_footer(text=str(user)))


def setup(bot):
    bot.add_cog(Helpful(bot))
