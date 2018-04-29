import asyncio

import discord
from discord.ext import commands

MONITOR_CHANNEL = 399852942213251083

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
            return m.id

class Monitor:

    def __init__(self, bot):
        self.bot = bot
        self.logged_users = []

    @commands.group(invoke_without_command=True)
    @commands.has_any_role('Staff')
    async def monitor(self, ctx, member: MemberID):
        if ctx.invoked_subcommand is not None:
            return
        self.logged_users += [member]
        member = await self.bot.get_user_info(member)
        await ctx.send(f'Now monitoring {member}.')

    @monitor.command(name="list")
    @commands.has_any_role('Staff')
    async def monitor_list(self, ctx):
        if self.logged_users:
            await ctx.send('Users currently getting logged:\n'+'\n'.join([self.bot.get_user(u) or u for u in self.logged_users]))
        else:
            await ctx.send('No users are getting logged atm.')

    @commands.command()
    @commands.has_any_role('Staff')
    async def unmonitor(self, ctx, member: MemberID):
        self.logged_users.remove(member)
        member = await self.bot.get_user_info(member)
        await ctx.send(f'No longer monitoring {member}.')

    async def on_member_join(self, member):
        if member.id in self.logged_users:
            ch = self.bot.get_channel(MONITOR_CHANNEL)
            await ch.send(f'{member.mention} joined the server.')

    async def on_member_remove(self, member):
        if member.id in self.logged_users:
            ch = self.bot.get_channel(MONITOR_CHANNEL)
            await ch.send(f'{member.mention} is no longer on the server.')

    async def log(self, logtype, user_id, channel, content, attachments=''):
        await self.bot.db.execute(
            f'INSERT INTO `monitorlog` (`type`, `user_id`, `channel`, `content`, `attachments`) '
            f'VALUES (%s, %s, %s, %s, %s)', (logtype, user_id, channel, content, attachments))

    async def on_message_delete(self, message):
        att = '\n'.join(x.url for x in message.attachments)
        await self.log('delete', message.author.id, message.channel.id, message.content, att)

    async def on_message_edit(self, before, after):
        if before.content != after.content:
            await self.log('edit', before.author.id, before.channel.id, before.content)

    async def on_command(self, ctx):
        await self.log('command', ctx.author.id, ctx.channel.id, ctx.message.content)

    # @commands.command()
    # async def deletes(self, ctx, target: DeleteTarget = None):
    #     if not target:
    #         target = ctx.channel.id
    #     deletes = await self.bot.db.fetch(
    #         'SELECT author, content FROM `monitorlog` WHERE type="delete" AND (`author`=%s OR `channel`=%s)',
    #         (target, target))
    #     await ctx.send('```\n' + '\n'.join(
    #         [f'{self.bot.get_user(author) or "?"} :{content}' for author, content in deletes]) + '```')

    @commands.group(invoke_without_command=True)
    @commands.has_role('Staff')
    async def deletes(self, ctx):
        if ctx.invoked_subcommand:
            return
        await ctx.send('deletes')

    @deletes.command(name='from')
    @commands.has_role('Staff')
    async def deletes_from(self, ctx, member: discord.Member):
        qry = f'SELECT content, attachments FROM monitorlog WHERE type="delete" AND user_id={member.id} ' \
              f'ORDER BY id DESC'
        rows = await self.bot.db.fetch(qry)

        if not rows:
            return await ctx.send('No deletes found')

        def callback(page):
            em = discord.Embed(title=f'Recent deletions from {member}')
            for c, a in rows[page * 5:page * 5 + 5]:
                a = '\n' + ' '.join([f'[image {i+1}]({link})' for i, link in enumerate(a.split('\n'))]) if a else ''
                em.add_field(name=member.display_name, value=c or '-' + a, inline=False)
            em.set_footer(text=f'Page {page+1}')
            return em

        await self.embed_paginator(ctx, callback)

    @deletes.command(name='in')
    @commands.has_role('Staff')
    async def deletes_in(self, ctx, channel: discord.TextChannel):
        qry = f'SELECT user_id, content, attachments FROM monitorlog WHERE type="delete" AND channel={channel.id} ' \
              f'ORDER BY id DESC'
        rows = await self.bot.db.fetch(qry)

        if not rows:
            return await ctx.send('No deletes found')

        def callback(page):
            em = discord.Embed(title=f'Recent deletions in {channel}')
            for u, c, a in rows[page * 5:page * 5 + 5]:
                member = ctx.bot.get_user(u)
                a = '\n' + ' '.join([f'[image {i+1}]({link})' for i, link in enumerate(a.split('\n'))]) if a else ''
                em.add_field(name=member.display_name if member else u, value=c or '-' + a, inline=False)
            em.set_footer(text=f'Page {page+1}')
            return em

        await self.embed_paginator(ctx, callback)

    async def embed_paginator(self, ctx, callback, index=0):
        buttons = ['◀', '▶', '🔄', '⏹']

        msg = await ctx.send(embed=callback(index))
        for button in buttons:
            await msg.add_reaction(button)

        while True:
            try:
                def check(r, u):
                    return u.id == ctx.author.id and r.message.id == msg.id and str(r) in buttons

                reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=120)
            except asyncio.TimeoutError:
                break
            else:
                await msg.remove_reaction(reaction, user)
                t = buttons.index(str(reaction))
                if t == 0:
                    if index > 0:
                        index -= 1
                        await msg.edit(embed=callback(index))
                elif t == 1:
                    index += 1
                    await msg.edit(embed=callback(index))
                elif t == 2:
                    await msg.edit(embed=callback(index))
                else:
                    break
        await msg.delete()


def setup(bot):
    bot.add_cog(Monitor(bot))
