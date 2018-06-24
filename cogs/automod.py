import re

import discord

INVITE_REGEX = "(https?:\/\/)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com\/invite)\/.+"


class Automod:
    """Kiara attempting to detect cunts and deal with them"""

    def __init__(self, bot):
        self.bot = bot
        self.inviteregex = re.compile(INVITE_REGEX)

    async def on_message(self, msg):
        if msg.guild is None:
            return

        # Check if message content contains an invite url
        invite = self.inviteregex.search(msg.content)
        if invite:
            # Ignore staff though
            if discord.utils.get(msg.author.roles, name="Staff") is None:
                await msg.delete()
                await msg.channel.send(f"{msg.author.mention} you sent an invite link, I deleted it for you.")


def setup(bot):
    bot.add_cog(Automod(bot))
