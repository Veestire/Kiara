import json
import random

import discord
from discord.ext import commands
from cogs.moderation import MemberID
STAFF_CHANNEL = 231008480079642625


async def generate_embed(title, image_url):
    embed = discord.Embed(title=title, colour=discord.Colour(0xd39466))
    embed.set_image(url=image_url)
    return embed


async def save_json(data):
    with open('/home/Kiara/data.json', 'w') as json_file_to_write:
        json.dump(data, json_file_to_write)


class BangAndTheThotIsGone:
    """Begone Thot meme command!"""

    def __init__(self, bot):
        self.bot = bot
        with open('/home/Kiara/data.json') as json_file:
            self.data = json.load(json_file)

    @commands.group(name="begonemanage")
    @commands.has_any_role('Staff')
    async def begone_manage(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid sub-command passed')

    @begone_manage.command()
    @commands.has_any_role('Staff')
    async def add_image(self, ctx, imageurl, memberid='Default'):
        try:
            self.data[memberid].append(imageurl)
            await ctx.send(f"Successfully added the image for {memberid}")
            await save_json(self.data)
        except KeyError as k:
            await ctx.send(f"Failed to add image for the MemberID: {k} "
                           f"\nMost likely cause of this is because the specified id does not exist in the"
                           f" data file!")

    @begone_manage.command()
    @commands.has_any_role('Staff')
    async def add_user(self, ctx, member: discord.Member):
        for role in member.roles:
            if role.name == "Staff":
                await ctx.send(f"Adding member {member.display_name} to the data file")
                self.data[str(member.id)] = []
                await save_json(self.data)
                return
        await ctx.send("member specified is not staff, therefore cannot be added")

    @begone_manage.command()
    @commands.has_any_role('Staff')
    async def remove_image(self, ctx, imageid: int, memberid='Default'):
        member_images = self.data[memberid]
        try:
            member_images.pop(imageid)
            self.data[memberid] = member_images
            await save_json(self.data)
        except Exception as e:
            await ctx.send(e)

    @begone_manage.command()
    @commands.has_any_role('Staff')
    async def list_images(self, ctx, memberid="Default"):
        member_images = self.data[memberid]
        for i in range(0, len(member_images)):
            await ctx.send(embed=await generate_embed(i, member_images[i]))

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
                            embed=await generate_embed(f'Banned {member}!',
                                                       random.choice(self.data[str(ctx.author.id)])))
                await ctx.send(
                    embed=await generate_embed(f'Banned {member}!', random.choice(self.data["Default"])))
            except Exception as e:
                await ctx.send(e)
        else:
            ch = self.bot.get_channel(STAFF_CHANNEL)
            member = await self.bot.get_user_info(member)
            await ch.send(f"<@&293008190843387911> {ctx.author.mention} requests banning {member.mention}.")
            await ctx.send('Your ban request has been received.')


def setup(bot):
    bot.add_cog(BangAndTheThotIsGone(bot))
