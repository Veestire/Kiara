import json
import random

import discord
from discord.ext import commands

STAFF_CHANNEL = 231008480079642625


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
            can_execute = ctx.author.id == ctx.bot.owner_id or \
                          ctx.author == ctx.guild.owner or \
                          ctx.author.top_role > m.top_role

            if not can_execute:
                raise commands.BadArgument('You cannot do this action on this user due to role hierarchy.')
            return m.id


class Bangandthethotisgone:
    """Begone Thot meme command!"""

    # Current staff members as of 04/01/2018
    # Alexstraza#2284 (154780079694675969)
    # Roo#6584 (211238461682876416)
    # ❄Axiself❄#6634 (256440172214878208)
    # Yuki#2520 (190007233919057920)
    # Tormund#3852 (238616410941554688)
    # ZamieltheHunter#4105 (182287810173206529)
    # Gala#8207 (73389450113069056)
    # Riiiina-Chan#9369 (265599587333570563)

    def __init__(self, bot):
        self.bot = bot
        with open('data.json') as json_file:
            self.data = json.load(json_file)

    async def generateEmbed(self, title, imageurl):
        embed = discord.Embed(title=title, colour=discord.Colour(0xd39466))
        embed.set_image(url=imageurl)
        return embed

    @commands.command(name="begone", aliases=["thot", "begonethot"])
    @commands.has_any_role('Staff')
    async def begone(self, ctx, member: MemberID, *, reason=None):
        permissions = ctx.channel.permissions_for(ctx.author)
        if getattr(permissions, 'ban_members', None):
            try:
                await ctx.guild.ban(discord.Object(id=member), reason=reason)
                member = await self.bot.get_user_info(member)
                if str(ctx.author.id) in self.data:
                    if self.data[str(ctx.author.id)]:
                        return await ctx.send(
                            embed=await self.generateEmbed(f'Banned {member}!',
                                                           random.choice(self.data[str(ctx.author.id)])))
                await ctx.send(
                    embed=await self.generateEmbed(f'Banned {member}!', random.choice(self.data["Default"])))
            except Exception as e:
                await ctx.send(e)
        else:
            ch = self.bot.get_channel(STAFF_CHANNEL)
            member = await self.bot.get_user_info(member)
            await ch.send(f"<@&293008190843387911> {ctx.author.mention} requests banning {member.mention}.")
            await ctx.send('Your ban request has been received.')

def setup(bot):
    bot.add_cog(Bangandthethotisgone(bot))
