import re


class Dev:

    def __init__(self, bot):
        self.bot = bot
        self.issue = re.compile(r'##(?P<number>[0-9]+)')

    async def on_message(self, message):
        if not message.guild:
            return

        m = self.issue.search(message.content)
        if m is not None:
            url = 'https://github.com/Nekorooni/Kiara/issues/'
            await message.channel.send(url + m.group('number'))


def setup(bot):
    bot.add_cog(Dev(bot))
