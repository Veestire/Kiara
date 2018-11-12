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

    @commands.command(aliases=['roulette', 'spin'])
    async def classicroulette(self, ctx, amount:int, choice):

        roulette = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14]
        spinemotes = [
        '<:r0:451726112423149568>', '<:r1:451726112381206538>','<:r2:451726112238600202>', '<:r3:451726112343719937>',
        '<:r4:451726111643140109>', '<:r5:451726112201113620>', '<:r6:451726112213696512>',
        '<:r7:451726112163102731>', '<:r8:451726112314097704>', '<:r9:451726111949193219>', '<:r10:451726112100450305>',
        '<:r11:451726111970295809>', '<:r12:451726112284868618>', '<:r13:451726112414892032>', '<:r14:451726112343588864>'
        ]
        pointer = ['<:line:451728056764334081>', '<:arrowup:451727652219518986>']

        colors = ['red', 'black', 'green']

        if amount<=0:
            return await ctx.send("Please bet more than 0")
        if choice:
            if choice.lower() not in colors:
                return await ctx.send("Please specify the color you wish to bet on. These are red, black, or green.")

        profile = await self.profiles.get_profile(ctx.author.id, ('coins',))
        if profile.coins < amount:
            return await ctx.send("You don't have enough gold to bet that much.")

        hit = random.choice(roulette)
        val1 = ((hit-1) % len(roulette))
        val3 = ((hit+1) % len(roulette))

        hitcolor = None
        if hit == 0:
            hitcolor = 'green'

        elif (hit % 2) == 0:
            hitcolor = 'red'

        elif (hit % 2) > 0:
            hitcolor = 'black'

        async with self.profiles.get_lock(ctx.author.id):
            profile = await self.profiles.get_profile(ctx.author.id, ('coins',))
            if hitcolor != None:
                if hitcolor == choice.lower():
                    if choice.lower() == "green":
                        await ctx.send(f"{spinemotes[val1]} {spinemotes[hit]} {spinemotes[val3]}\n"
                                       f"{pointer[0]} {pointer[1]} {pointer[0]}\n"
                                       f"It landed on {hitcolor}! You win {amount*15} gold!")
                        profile.coins += (amount*10)

                    else:
                        await ctx.send(f"{spinemotes[val1]} {spinemotes[hit]} {spinemotes[val3]}\n"
                                       f"{pointer[0]} {pointer[1]} {pointer[0]}\n"
                                       f"The roulette landed on {hit}! You bet on {hitcolor}, you win {amount*2} gold!")
                        profile.coins += (amount*2)

                else:
                    await ctx.send(f"{spinemotes[val1]} {spinemotes[hit]} {spinemotes[val3]}\n"
                                   f"{pointer[0]} {pointer[1]} {pointer[0]}\n"
                                   f"The roulette landed on {hit} which is {hitcolor}! Sorry, you lose {amount} gold.")
                    profile.coins -= amount

            await profile.save(self.bot.db)



def setup(bot):
    bot.add_cog(Casino(bot))
