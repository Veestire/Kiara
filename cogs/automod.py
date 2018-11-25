import asyncio
import datetime
import re

import discord

INVITE_REGEX = "(https?:\/\/)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com\/invite)\/.+"


class Automod:
    """Kiara attempting to detect cunts and deal with them"""

    def __init__(self, bot):
        self.bot = bot
        self.inviteregex = re.compile(INVITE_REGEX)

        self.moderation = bot.get_cog("Moderation")

        self.bg_task = bot.loop.create_task(self.update_user_log())

    def __unload(self):
        self.bg_task.cancel()

    async def update_user_log(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(497088811486937098)
        try:
            while not self.bot.is_closed():
                await channel.edit(name=f"Total Users > {len(channel.guild.members)}")
                await asyncio.sleep(3600)
        except Exception as e:
            print(e)

    async def invite_check(self, msg):
        if msg.guild is None:
            return

        # Check if message content contains an invite url
        invite = self.inviteregex.search(msg.content)
        if invite:
            # Ignore staff though
            if discord.utils.get(msg.author.roles, name="Staff") is None:
                await msg.delete()
                await msg.channel.send(f"{msg.author.mention} you sent an invite link, I deleted it for you.")
                await msg.author.add_roles(discord.utils.get(msg.guild.roles, id=348331525479071745))

    async def on_message(self, msg):
        if len(list(filter(lambda m: m.author.id == msg.author.id and m.created_at > datetime.datetime.now() - datetime.timedelta(seconds=2), self.bot._connection._messages))) >= 5:
            await self.moderation.mute_user_id(msg.author.id, 5, "Auto mute")
            await self.moderation.warn_user(msg.author.id, self.bot.user.id, "Auto-mute: Possible spam")

        await self.invite_check(msg)

    async def on_message_edit(self, before, after):
        await self.invite_check(after)

    async def on_member_join(self, member):
        if member.created_at > datetime.datetime.now() - datetime.timedelta(days=1):
            await member.send("Your account has been kicked for being under a day old to prevent malicious users joining the server.")
            await member.kick(reason="Auto-kick for suspicious account")


def setup(bot):
    bot.add_cog(Automod(bot))
