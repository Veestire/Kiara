from discord.ext import commands


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def session(self):
        return self.bot.session

    @property
    def redis(self):
        return self.bot.redis

    async def confirm(self):
        await self.message.add_reaction('greentick:526847326812110933')
