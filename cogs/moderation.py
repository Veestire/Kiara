import datetime

from .utils import time
from discord.ext import commands

import asyncio
import discord
import random


STAFF_CHANNEL = 231008480079642625
MUTED_ROLE = 348331525479071745

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

class BannedMember(commands.Converter):
    async def convert(self, ctx, argument):
        ban_list = await ctx.guild.bans()
        try:
            member_id = int(argument, base=10)
            entity = discord.utils.find(lambda u: u.user.id == member_id, ban_list)
        except ValueError:
            entity = discord.utils.find(lambda u: str(u.user) == argument, ban_list)

        if entity is None:
            raise commands.BadArgument("Not a valid previously-banned member.")
        return entity

class Moderation:
    """Moderation commands"""

    def __init__(self, bot):
        self.bot = bot
        self.timers = bot.get_cog('Timers')
        self.stafflog = bot.get_cog('Stafflog')

    @commands.command()
    @commands.has_any_role('Staff')
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        permissions = ctx.channel.permissions_for(ctx.author)
        if getattr(permissions, 'kick_members', None):
            try:
                await ctx.guild.kick(member, reason=reason)
                await ctx.send(f'Kicked {member}!')
            except Exception as e:
                await ctx.send(e)
        else:
            ch = self.bot.get_channel(STAFF_CHANNEL)
            await ch.send(f"<@&293008190843387911> {ctx.author.mention} requests kicking {member.mention}.")
            await ctx.send('Your kick request has been received.')

    @commands.command()
    @commands.has_any_role('Staff')
    async def ban(self, ctx, member: MemberID, *, reason=None):
        permissions = ctx.channel.permissions_for(ctx.author)
        if getattr(permissions, 'ban_members', None):
            try:
                await ctx.guild.ban(discord.Object(id=member), reason=reason)
                member = await self.bot.get_user_info(member)
                await ctx.send(f'Banned {member}!')
            except Exception as e:
                await ctx.send(e)
        else:
            ch = self.bot.get_channel(STAFF_CHANNEL)
            member = await self.bot.get_user_info(member)
            await ch.send(f"<@&293008190843387911> {ctx.author.mention} requests banning {member.mention}.")
            await ctx.send('Your ban request has been received.')


    @commands.command()
    @commands.has_any_role('Staff')
    async def unban(self, ctx, member: BannedMember, *, reason=None):
        permissions = ctx.channel.permissions_for(ctx.author)
        if getattr(permissions, 'ban_members', None):
            try:
                await ctx.guild.unban(member.user, reason=reason)
                await ctx.send(f'Unbanned {member.user}!')
            except Exception as e:
                await ctx.send(e)
        else:
            ch = self.bot.get_channel(STAFF_CHANNEL)
            await ch.send(f"{ctx.author.mention} requests unbanning {member.user.mention}.")
            await ctx.send('Your uban request has been received.')

    @commands.command()
    @commands.has_role('Staff')
    async def mute(self, ctx, member: discord.Member, minutes: int = 5, *, reason = None):
        await member.add_roles(discord.utils.get(ctx.guild.roles, id=MUTED_ROLE))
        await self.timers.create_timer('unmute', datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes),
                                       [ctx.guild.id, member.id])
        await self.stafflog.make_case(member, f'Mute ({minutes} minute{"s" if minutes!=1 else ""})', reason, ctx.author)

    async def on_unmute_event(self, guild_id, user_id):
        guild = self.bot.get_guild(guild_id)
        member = guild.get_member(user_id)
        await member.remove_roles(discord.utils.get(guild.roles, id=MUTED_ROLE))

    @commands.command(aliases=['finduser'])
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def userfind(self, ctx, *, search):
        found = []

        if not ctx.guild.chunked:
            await self.bot.request_offline_members(ctx.guild)

        for m in ctx.guild.members:
            if search.lower() in m.name.lower():
                found += [m]
        if found:
            await ctx.send('Matches users:```\n'+'\n'.join([f'{m} ({m.id})' for m in found])+'```')
        else:
            await ctx.send('Found nothing')

    @commands.command(aliases=['newmembers'])
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def newusers(self, ctx, *, count=5):
        """Tells you the newest members of the server.
        This is useful to check if any suspicious members have
        joined.
        The count parameter can only be up to 25.
        """
        count = max(min(count, 25), 5)

        if not ctx.guild.chunked:
            await self.bot.request_offline_members(ctx.guild)

        members = sorted(ctx.guild.members, key=lambda m: m.joined_at, reverse=True)[:count]

        e = discord.Embed(title='New Members', colour=discord.Colour.green())

        for member in members:
            body = f'joined {time.time_ago(member.joined_at)}, created {time.time_ago(member.created_at)}'
            e.add_field(name=f'{member} (ID: {member.id})', value=body, inline=False)

        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Moderation(bot))
