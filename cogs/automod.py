import re

INVITE_REGEX = "(https?:\/\/)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com\/invite)\/.+"


class Automod:
    """Kiara attempting to detect cunts and deal with them"""

    def __init__(self, bot):
        self.bot = bot
        self.inviteregex = re.compile(INVITE_REGEX)

    async def on_message(self, msg):
        # Check if message content contains an invite url
        invite = self.inviteregex.search(msg.content)
        if invite:
            await msg.delete()
            await msg.channel.send("No")


def setup(bot):
    bot.add_cog(Automod(bot))
