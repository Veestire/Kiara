import discord

class Silhouette:

    def __init__(self, bot):
        self.bot = bot

    async def on_member_join(self, member):
        if member.name.lower() == 'silhouette':
            await member.ban(reason='Spam bot')

def setup(bot):
    bot.add_cog(Silhouette(bot))
