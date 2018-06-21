import datetime
import sys
import traceback

import discord
from discord.ext import commands
import aiohttp
import aioredis

from cogs.utils.config import Config
from cogs.utils.db import DB

desc = 'A personal bot for Waifu Worshipping'

config = Config()


class Kiara(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix=config.prefix, description=desc, pm_help=None, help_attrs=dict(hidden=True),
                         game=discord.Game(name='~help'))
        self.load_cogs()
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.db = DB(config.MYSQL_HOST, config.MYSQL_USER, config.MYSQL_PASSWORD, config.MYSQL_DATABASE, self.loop)
        self.redis = self.loop.run_until_complete(aioredis.create_connection('redis://redis', loop=self.loop))

    def load_cogs(self):
        for cog in config.base_cogs.split():
            try:
                self.load_extension(cog)
            except Exception as e:
                print(f"Cog '{cog}' failed to load.", file=sys.stderr)
                traceback.print_exc()

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = datetime.datetime.utcnow()
        print(f'Ready: {self.user} (ID: {self.user.id})')
        print(f'Discord {discord.__version__}')

    async def on_resumed(self):
        print('Resumed..')

    async def on_command_error(self, ctx, error):
        # TODO: Add extra error handling
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send('This command is only for use inside guilds.')
        elif isinstance(error, commands.DisabledCommand):
            pass
        elif isinstance(error, commands.BadArgument):
            await ctx.send(error)
        elif isinstance(error, commands.CommandInvokeError):
            print(f'In {ctx.command.qualified_name}:', file=sys.stderr)
            traceback.print_tb(error.original.__traceback__)
            print(f'{error.original.__class__.__name__}: {error.original}', file=sys.stderr)

    @property
    def config(self):
        return config

    def run(self):
        super().run(config.token)


if __name__ == '__main__':
    rub = Kiara()
    rub.run()
