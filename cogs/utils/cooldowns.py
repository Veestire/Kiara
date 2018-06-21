from discord.ext import commands


def basic_cooldown(seconds):
    async def predicate(ctx):
        cd = await ctx.redis.ttl()
    return commands.check(predicate)
