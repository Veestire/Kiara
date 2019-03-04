import discord
from discord.ext import commands

import asyncio
import traceback


def get_color_role(member):
    for role in member.roles:
        if role.color == member.color:
            return role

base_colors = [
     ("Red", 424579184216506368, 30),
     ("Yellow", 424579315066208276, 30),
     ("Green", 424579385983762432, 30),
     ("Orange", 424579446578872332, 30),
     ("Cyan", 424579523363733507, 30),
     ("Blue", 424579641802752000, 30),
     ("Purple", 424579707573633024, 30),
     ("Pink", 424579770240466951, 30),
     ("Charcoal", 424579833994149888, 30),
     ("Light Grey", 488187345565122565, 30),
 ]


class Intro(commands.Cog):
    """A cog handling the intro stuff"""

    legal = "Welcome to Waifu Worshipping, the home of all your lewd socialising needs! " \
            "Please make sure to read over #information and #rules to learn the essentials.\n" \
            "Also understand that due to the content of the server, all users are required to be over the age of 18.\n" \
            "By continuing with these questions, you confirm that you are of legal age.\n\n" \
            "**When you're ready to receive your roles, please reply with the following: **`begin`"
    questions = [
        ('Are you happy to receive messages from other users in the server?', 353019520983629824),
        ('Are you interested in being informed about all future server-wide events? (Movie nights, gaming events, and other fun activities)', 347689132908085248),
        ('Are you interested in seeing NSFW content?', 371251751564869632),
        ('Are you interested in roleplay channels?', 389376686745059329),
        ("Are you interested in the 'Weekly Waifu' channels? These are channels dedicated to posting images of the chosen waifu of the week, who is used for the server icon.", 549542288020471808)
    ]

    def __init__(self, bot):
        self.bot = bot
        self.active_intros = []

    @commands.command()
    async def newintro(self, ctx):
        await self.run_intro(ctx.author)

    @commands.command()
    @commands.has_role('Staff')
    async def activeintros(self):
        pass

    # @commands.Cog.listener()
    # async def on_member_join(self, member):
    #     if member.guild.id == self.bot.config.guild_id:
    #         # Start the intro if the user types anything before 10 mins, otherwise start the intro.
    #         try:
    #             msg = await self.bot.wait_for('message', check=lambda m: m.author.id == member.id, timeout=300)
    #             if 'intro' in msg.content:
    #                 return
    #         except asyncio.TimeoutError:
    #             pass
    #             await self.run_intro(member)

    async def run_intro(self, member):
        guild = self.bot.get_guild(self.bot.config.guild_id)

        if not isinstance(member, discord.Member):
            member = guild.get_member(member.id)

        emojis = [self.bot.get_emoji(emoji_id) for emoji_id in [526847326812110933, 526847326669504554]]
        async def ask(text):
            m = await member.send(text)
            for emoji in emojis:
                await m.add_reaction(emoji)

            def check(r, u):
                return u.id == member.id and r.emoji in emojis

            r, u = await self.bot.wait_for('reaction_add', check=check, timeout=120)

            return r.emoji == emojis[0]

        # The actual intro
        roles_to_add = []
        try:
            await self.bot.wait_for('message', check=lambda m: m.content.lower() == 'begin' and m.author == member, timeout=300)

            for question, role_id in self.questions:
                if await ask(question):
                    roles_to_add += [role_id]

            # If the user hasn't claimed a free color
            if not await self.bot.redis.exists(f"claimedcolor:{member.id}"):
                if await ask('Would you like a colored name for on the server?'):
                    owned = [r[0] for r in await self.bot.db.fetch(f'SELECT color FROM colors WHERE user_id={member.id}')]
                    await member.send("Which of the following colours would you like?\n"
                                      f"{', '.join([i[0] for i in base_colors])} or `none`")
                    c = await self.bot.wait_for('message', check=lambda m: m.author.id == member.id and m.guild is None, timeout=120)
                    for name, color_code, price in base_colors:
                        if c.content.lower() == name.lower() and color_code not in owned:
                            await self.bot.db.execute(
                                f"INSERT INTO colors (user_id, color) VALUES ({member.id}, {color_code})")
                            await self.bot.redis.set(f"claimedcolor:{member.id}", f"{name}")
                            roles_to_add += [color_code]
                            break
        except asyncio.TimeoutError:
            await member.send('Sorry, you took too long to answer. Use `~intro` if you want to start over.')
        except Exception as e:
            traceback.print_tb(e.__traceback__)
        else:
            await member.send("Please give me a few seconds to finalize everything.")

            fresh = discord.utils.get(member.roles, id=373122164544765953) is None
            roles_to_add += [373122164544765953]  # Member role

            all_role_ids = [i[1] for i in self.questions]

            await member.remove_roles(*[guild.get_role(role_id) for role_id in set(all_role_ids)-set(roles_to_add)])
            await member.add_roles(*[guild.get_role(role_id) for role_id in roles_to_add])

            await member.send('Thank you for answering, the appropriate roles have been assigned to you! '
                              'If there are any issues please contact a staff member, they will happily assist you.')

            # Send a log message if the user is new
            if fresh:
                monitorlog = self.bot.get_cog('Monitor')
                if monitorlog:
                    await monitorlog.post_member_log(member)
        finally:
            self.active_intros.remove(member.id)


def setup(bot):
    bot.add_cog(Intro(bot))
