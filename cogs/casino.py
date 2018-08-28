import random
import discord
from discord.ext import commands


class Casino:
    """Temporary casino so you can start gambling"""

    def __init__(self, bot):
        self.bot = bot
        self.profiles = bot.get_cog("Profiles")

    @commands.command()
    async def coinflip(self, ctx, amount: int, choice=None):
        if amount <= 0:
            return await ctx.send("Please bet more than 0")
        if choice:
            if choice.lower() not in ['heads', 'tails']:
                return await ctx.send("Please pick either `heads` or `tails`.")
        else:
            choice = 'heads'

        profile = await self.profiles.get_profile(ctx.author.id, ('coins',))
        if profile.coins < amount:
            return await ctx.send("You don't have enough gold to bet that much.")

        win = random.choice(['heads', 'tails'])

        async with self.profiles.get_lock(ctx.author.id):
            profile = await self.profiles.get_profile(ctx.author.id, ('coins',))

            if win == choice:
                await ctx.send(f"The coin landed on {win}.\nCongrats you won {int(amount*.9)} gold.")
                profile.coins += int(amount*.9)
            else:
                await ctx.send(f"The coin landed on {win}.\nSorry, you lost {amount} gold")
                profile.coins -= amount
            await profile.save(self.bot.db)


def setup(bot):
    bot.add_cog(Casino(bot))
