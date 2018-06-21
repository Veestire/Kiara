from discord.ext import commands


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.redis = self.bot.redis

    @property
    def session(self):
        return self.bot.session

    @property
    def rediss(self):
        return self.bot.redis