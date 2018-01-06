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


class BangAndTheThotIsGone:
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
        with open('/home/Kiara/data.json') as json_file:
            self.data = json.load(json_file)

    async def save_json(self, data):
        with open('/home/Kiara/data.json', 'w') as json_file_to_write:
            json.dump(data, json_file_to_write)

    async def generate_embed(self, title, image_url):
        embed = discord.Embed(title=title, colour=discord.Colour(0xd39466))
        embed.set_image(url=image_url)
        return embed

    @commands.group(name="BegoneManage")
    async def begone_manage(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid subcommand passed')

    @begone_manage.command()
    @commands.has_any_role('Staff')
    async def add_image(self, ctx, ImageURL, memberID='Default'):
        self.data[memberID].append(ImageURL)
        await self.save_json(self.data)

    @begone_manage.command()
    @commands.has_any_role('Staff')
    async def remove_image(self, ctx, ImageID: int, memberID='Default'):
        member_images = self.data[memberID]
        try:
            member_images.pop(ImageID)
            self.data[memberID] = member_images
            await self.save_json(self.data)
        except Exception as e:
            await ctx.send(e)

    @begone_manage.command()
    async def list_images(self, ctx, memberID="Default"):
        member_images = self.data[memberID]
        for i in range(0, len(member_images)):
            await ctx.send(embed=await self.generate_embed(i, member_images[i]))

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
                            embed=await self.generate_embed(f'Banned {member}!',
                                                            random.choice(self.data[str(ctx.author.id)])))
                await ctx.send(
                    embed=await self.generate_embed(f'Banned {member}!', random.choice(self.data["Default"])))
            except Exception as e:
                await ctx.send(e)
        else:
            ch = self.bot.get_channel(STAFF_CHANNEL)
            member = await self.bot.get_user_info(member)
            await ch.send(f"<@&293008190843387911> {ctx.author.mention} requests banning {member.mention}.")
            await ctx.send('Your ban request has been received.')

def setup(bot):
    bot.add_cog(BangAndTheThotIsGone(bot))
