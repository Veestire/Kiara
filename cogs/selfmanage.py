import asyncio
import traceback

import discord
from discord.ext import commands

from cogs.economy import base_colors

def get_color_role(member):
    for role in member.roles:
        if role.color == member.color:
            return role

GUILD_ID = 215424443005009920

class Selfmanage:
    """A cog for managing yourself"""

    all_roles = [
        353019520983629824, 347689132908085248, 371251751564869632,
        373135777955315712, 373135762230607882, 389376686745059329
    ]
    legal = "Welcome to Waifu Worshipping, the home of all your lewd socialising needs! " \
            "Please make sure to read over #information and #rules to learn the essentials.\n" \
            "Also understand that due to the content of the server, all users are required to be over the age of 18.\n"\
            "By continuing with these questions, you confirm that you are of legal age.\n\n" \
            "**When you're ready to receive your roles, please reply with the following: **`begin`"
    questions = [
        ('Are you happy to receive messages from other users in the server?', 353019520983629824),
        ('Are you interested in being informed about all future server-wide events? (Movie nights, gaming events, and other fun activities)', 347689132908085248),
        ('Are you interested in seeing NSFW content?', 371251751564869632),
        ('Are you interested in roleplay channels?', 389376686745059329)
    ]

    def __init__(self, bot):
        self.bot = bot
        self.active_intros = []
        self.profiles = bot.get_cog("Profiles")

    async def on_member_join(self, member):
        if member.guild.id == GUILD_ID:
            try:
                msg = await self.bot.wait_for('message', check=lambda m: m.author.id == member.id, timeout=300)
                if 'intro' in msg.content:
                    return
            except asyncio.TimeoutError:
                pass
            await self.questionare(member.guild, member)

    @commands.command()
    async def intro(self, ctx):
        if ctx.author.id in self.active_intros:
            return await ctx.send("You're already doing the intro.")
        guild = self.bot.get_guild(GUILD_ID) or ctx.guild
        if not guild:
            return
        if ctx.guild:
            await ctx.send(f'{ctx.author.mention} I sent you a DM!')
        await self.questionare(guild, guild.get_member(ctx.author.id))

    async def questionare(self, guild, member):
        if member.id in self.active_intros:
            return
        else:
            try:
                await member.send(self.legal)
            except discord.errors.Forbidden:
                return
            self.active_intros += [member.id]
        roles_to_add = []

        fresh = discord.utils.get(member.roles, id=373122164544765953) is None

        try:
            await self.bot.wait_for('message',
                                    check=lambda m: m.content.lower() == 'begin' and m.author == member, timeout=300)
            for question, role in self.questions:
                if await self.ask_question(member, question):
                    roles_to_add.append(discord.utils.get(guild.roles, id=role))

            if not await self.bot.redis.exists(f"claimedcolor:{member.id}"):
                await member.send("As thanks for completing the intro, I'm going to give you a free role color!\n"
                                  "These colors are the following:\n"
                                  f"{', '.join([i[0] for i in base_colors])}\n"
                                  "Please tell me which one you'd like!\n"
                                  "Or... you can type `none` instead and I'll add 30 gold to your server balance!")
                if await self.free_color(member) != False:
                    await member.send("I've added this color to your inventory~\nYou can check your owned colors with "
                                      "`!colors` and equip one with `!setcolor [color]`!")

        except asyncio.TimeoutError:
            try:
                await member.send('Sorry, you took too long to answer. Use `~intro` if you want to start over.')
            except:
                pass
            self.active_intros.remove(member.id)
        else:
            try:
                roles_to_add.append(discord.utils.get(guild.roles, id=373122164544765953))
                await member.send("Please give me a few seconds to finalize everything.")
                await member.remove_roles(*[discord.utils.get(guild.roles, id=x) for x in self.all_roles])
                await member.add_roles(*roles_to_add)
                await member.send('Thank you for answering, the appropriate roles have been assigned to you! If there are any issues, please contact a staff member and they will happily assist you.')
                if fresh:
                    monitorlog = self.bot.get_cog('Monitor')
                    await monitorlog.post_member_log(member)
            except Exception as e:
                traceback.print_tb(e.__traceback__)
            self.active_intros.remove(member.id)


    async def ask_question(self, user, question):
        def check(m):
            return isinstance(m.channel, discord.DMChannel) and m.author == user and is_answer(m.content)

        def is_answer(c):
            return 'y' in c.lower() or 'n' in c.lower()

        await user.send(question+' `yes / no`')

        m = await self.bot.wait_for('message', check=check, timeout=120)
        if 'y' in m.content.lower():
            await m.add_reaction('✅')
            return True
        else:
            return False

    async def free_color(self, user):
        owned = [r[0] for r in await self.bot.db.fetch(f'SELECT color FROM colors WHERE user_id={user.id}')]
        c = await self.bot.wait_for('message', check=lambda m:m.author == user and m.guild is None,
        timeout=120)
        for name, color_code, price in base_colors:
            if (c.content.lower() == name.lower()) and color_code not in owned:
                await self.bot.db.execute(f"INSERT INTO colors (user_id, color) VALUES ({user.id}, {color_code})")
                await self.bot.redis.set(f"claimedcolor:{user.id}", f"{name}")
                break

        else:
            async with self.profiles.get_lock(user.id):
                profile = await self.profiles.get_profile(user.id, ('coins',))
                profile.coins += 30
                await profile.save(self.bot.db)
                await self.bot.redis.set(f"claimedcolor:{user.id}", "gold")
                await user.send("I've added 30 gold to your balance. Use `!shop` to go buy something~")
            return False


def setup(bot):
    bot.add_cog(Selfmanage(bot))
