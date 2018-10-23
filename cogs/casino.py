import random
import discord
from discord.ext import commands


class Casino:
    """Temporary casino so you can start gambling"""

    def __init__(self, bot):
        self.bot = bot
        self.profiles = bot.get_cog("Profiles")

    @commands.command(aliases=['cf'])
    async def coinflip(self, ctx, amount: int, choice=None):
        """Bet some money on flipping a coin"""
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
        emote = '<:aa:474567347588431893>' if win == 'tails' else '<:aa:474567346833588244>'

        async with self.profiles.get_lock(ctx.author.id):
            profile = await self.profiles.get_profile(ctx.author.id, ('coins',))

            if win == choice.lower():
                await ctx.send(f"The coin landed on {win}. {emote}\nCongrats you won {amount} gold.")
                profile.coins += amount
            else:
                await ctx.send(f"The coin landed on {win}. {emote}\nSorry, you lost {amount} gold")
                profile.coins -= amount
            await profile.save(self.bot.db)

    @commands.command()
    async def russianroulette(self, ctx, *participants: discord.Member):
        """Play an innocent game of russian roulette. Winner dies."""
        chamber = [0, 0, 0, 0, 0, 1]
        random.shuffle(chamber)
        participants = list(participants)
        random.shuffle(participants)
        for i, b in enumerate(chamber):
            current = participants[i % len(participants)]
            await ctx.send(embed=discord.Embed(description=f"{current} is next, type `shoot` or literally anything else"))
            msg = await self.bot.wait_for('message', check=lambda m: m.author in participants)
            if b:
                await ctx.send(embed=discord.Embed(description=f"{current} lost"))
                break
            else:
                await ctx.send(embed=discord.Embed(description="Lucky"))


def setup(bot):
    bot.add_cog(Casino(bot))
