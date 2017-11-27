import asyncio
import datetime

import discord
from discord.ext import commands

GUILD_ID = 215424443005009920
LOG_CHANNEL = 364983647087886336

class Stafflog:
    """Logging the bans~"""

    def __init__(self, bot):
        self.bot = bot

    async def make_case(self, user, action, reason=None):
        date = datetime.datetime.utcnow()
        ch = self.bot.get_channel(LOG_CHANNEL)
        msg = await ch.send('Case')
        _, c_id = await self.bot.db.execute(f'INSERT INTO stafflog (message_id, user_id, action, reason, date) '
                                            f'VALUES ({msg.id}, {user.id}, "{action}", "{reason}", "{date}")')

        if reason is None:
            reason = f'`~reason {c_id} [reason]`'
        fmt = f"User: {user} ({user.id})\nAction: {action}\nReason: {reason}"
        em = discord.Embed(description=fmt)
        em.timestamp = date
        em.set_footer(text=f'Case #{c_id}')

        await msg.edit(content='', embed=em)

    @commands.command()
    @commands.has_role('Staff')
    async def reason(self, ctx, case_id: int, *, reason):
        m_id, = await self.bot.db.fetchone(
            f'SELECT message_id FROM stafflog WHERE id={case_id}')
        msg = await self.bot.get_channel(LOG_CHANNEL).get_message(m_id)
        em = msg.embeds[0].to_dict()
        # Keep the old info, so the username doesn't change in case the it's changed.
        em['description'] = '\n'.join(em['description'].split('\n')[:2]) + f"\nReason: {reason}"
        await msg.edit(embed=discord.Embed.from_data(em))
        await ctx.message.delete()

    async def on_member_remove(self, member):
        if member.guild.id != GUILD_ID:
            return
        await asyncio.sleep(2)
        log = await member.guild.audit_logs(action=discord.AuditLogAction.kick).get(target__id=member.id)
        if log:
            await self.make_case(member, 'Kick', log.reason)

    async def on_member_ban(self, member):
        if member.guild.id != GUILD_ID:
            return
        await asyncio.sleep(2)
        log = await member.guild.audit_logs(action=discord.AuditLogAction.ban).get(target__id=member.id)
        if log:
            await self.make_case(member, 'Ban', log.reason)

    async def on_member_unban(self, guild, member):
        if guild.id != GUILD_ID:
            return
        await asyncio.sleep(2)
        log = await member.guild.audit_logs(action=discord.AuditLogAction.unban).get(target__id=member.id)
        if log:
            await self.make_case(member, 'Unban', log.reason)

def setup(bot):
    bot.add_cog(Stafflog(bot))
