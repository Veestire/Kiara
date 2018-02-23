from discord.ext import commands
import discord


STAR_CHANNEL = 415464201809690624
STAR_THRESHOLD = 8

IGNORED = [271695900718399488]

class Starboard:
    """Starboard pinning quotes stuff"""

    async def on_raw_reaction_add(self, emoji, message_id, channel_id, user_id):
        if channel_id == STAR_CHANNEL:
            return
        if channel_id in IGNORED:
            return
        if str(emoji) != '\N{WHITE MEDIUM STAR}':
            return
        channel = self.bot.get_channel(channel_id)
        msg = await channel.get_message(message_id)
        if await self.count_stars(msg) < STAR_THRESHOLD:
            return

        r = await self.bot.db.fetchone(f'SELECT * FROM `starboard` WHERE message_id={message_id}')
        if r:
            pass
        else:
            emb = self.make_embed(msg)
            post = await self.bot.get_channel(STAR_CHANNEL).send(embed=emb)
            await self.bot.db.execute(
                f'INSERT INTO `starboard` (message_id, bot_message_id) VALUES ({message_id}, {post.id})')

    async def on_raw_reaction_remove(self, emoji, message_id, channel_id, user_id):
        pass

    def make_embed(self, msg):
        emb = discord.Embed(description=msg.content)
        emb.set_author(name=msg.author.name, icon_url=msg.author.avatar_url_as(size=64))
        if msg.attachments:
            emb.set_image(url=msg.attachments[0].url)
        elif msg.embeds:
             emb.set_image(url=msg.embeds[0].image.url)
        emb.timestamp = msg.created_at
        return emb

    async def count_stars(self, msg):
        n = 0
        u = []
        for r in msg.reactions:
            if str(r.emoji) == '\N{WHITE MEDIUM STAR}':
                async for user in r.users():
                    if user.id not in u:
                        n += 1
                        u.append(user.id)
        return n

    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Starboard(bot))
