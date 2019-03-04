import asyncio
import copy
import inspect
import io
import textwrap
import time
import traceback
from contextlib import redirect_stdout

import discord
from discord.ext import commands


def cogname(name):
    return name if name.startswith('cogs.') else f'cogs.{name}'


class Admin(commands.Cog):
    """Admin-only commands that make the bot dynamic."""

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.sessions = set()

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author) or ctx.author.id in [211238461682876416, 73389450113069056]

    def get_syntax_error(self, e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    @commands.command(hidden=True)
    async def load(self, ctx, *, cog: cogname):
        """Loads a cog."""
        try:
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send(embed=discord.Embed(title=f'Loaded {cog}', color=0x54d154))

    @commands.command(hidden=True)
    async def unload(self, ctx, *, cog: cogname):
        """Unloads a cog."""
        if self.bot.extensions.get(cog):
            self.bot.unload_extension(cog)
            await ctx.send(embed=discord.Embed(title=f'Unloaded {cog}', color=0x54d154))
        else:
            await ctx.send(embed=discord.Embed(title="That cog wasn't loaded", color=0xd15454))

    @commands.command(name='reload', hidden=True)
    async def _reload(self, ctx, *, cog: cogname):
        """Reloads a cog."""
        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send(embed=discord.Embed(title=f'Reloaded {cog}', color=0x54d154))

    @commands.command(hidden=True, name='eval')
    async def _eval(self, ctx, *, body: str):
        """Evaluates a code"""

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                async with ctx.typing():
                    start = time.perf_counter()
                    ret = await func()
                    dt = (time.perf_counter() - start) * 1000.0
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    fmt=f'```py\n{value}\n```\n*Took {dt:.2f} ms*'
                else:
                    fmt=f'*Took {dt:.2f} ms*'
            else:
                self._last_result = ret
                fmt= f'```py\n{value}{ret}\n```\n*Took {dt:.2f} ms*'
            if len(fmt)>2000:
                fp = io.BytesIO(fmt.encode('utf-8'))
                await ctx.send('Output too large', file=discord.File(fp, 'output.txt'))
            else:
                await ctx.send(fmt)

    @commands.command(pass_context=True, hidden=True)
    async def repl(self, ctx):
        """Launches an interactive REPL session."""
        variables = {
            'ctx': ctx,
            'bot': self.bot,
            'message': ctx.message,
            'guild': ctx.guild,
            'channel': ctx.channel,
            'author': ctx.author,
            '_': None,
        }

        if ctx.channel.id in self.sessions:
            await ctx.send('Already running a REPL session in this channel. Exit it with `quit`.')
            return

        self.sessions.add(ctx.channel.id)
        await ctx.send('Enter code to execute or evaluate. `exit()` or `quit` to exit.')

        def check(m):
            return m.author.id == ctx.author.id and \
                   m.channel.id == ctx.channel.id and \
                   m.content.startswith('`')

        while True:
            try:
                response = await self.bot.wait_for('message', check=check, timeout=10.0 * 60.0)
            except asyncio.TimeoutError:
                await ctx.send('Exiting REPL session.')
                self.sessions.remove(ctx.channel.id)
                break

            cleaned = self.cleanup_code(response.content)

            if cleaned in ('quit', 'exit', 'exit()'):
                await ctx.send('Exiting.')
                self.sessions.remove(ctx.channel.id)
                return

            executor = exec
            if cleaned.count('\n') == 0:
                # single statement, potentially 'eval'
                try:
                    code = compile(cleaned, '<repl session>', 'eval')
                except SyntaxError:
                    pass
                else:
                    executor = eval

            if executor is exec:
                try:
                    code = compile(cleaned, '<repl session>', 'exec')
                except SyntaxError as e:
                    await ctx.send(self.get_syntax_error(e))
                    continue

            variables['message'] = response

            fmt = None
            stdout = io.StringIO()

            try:
                with redirect_stdout(stdout):
                    result = executor(code, variables)
                    if inspect.isawaitable(result):
                        result = await result
            except Exception as e:
                value = stdout.getvalue()
                fmt = f'```py\n{value}{traceback.format_exc()}\n```'
            else:
                value = stdout.getvalue()
                if result is not None:
                    fmt = f'```py\n{value}{result}\n```'
                    variables['_'] = result
                elif value:
                    fmt = f'```py\n{value}\n```'

            try:
                if fmt is not None:
                    if len(fmt) > 2000:
                        await ctx.send('Content too big to be printed.')
                    else:
                        await ctx.send(fmt)
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                await ctx.send(f'Unexpected error: `{e}`')

    @commands.command(hidden=True)
    async def sql(self, ctx, *, query: str):
        """Run some SQL."""
        await ctx.send(await self.bot.db.fetch(query))

    @commands.command(hidden=True)
    async def do(self, ctx, times: int, *, command):
        """Repeats a command a specified number of times."""
        msg = copy.copy(ctx.message)
        msg.content = command
        for i in range(times):
            await self.bot.process_commands(msg)
            await asyncio.sleep(1)

    @commands.command(hidden=True)
    async def runas(self, ctx, user: discord.User, *, command):
        msg = copy.copy(ctx.message)
        msg.content = command
        msg.author = user

        await self.bot.process_commands(msg)

    @commands.command(hidden=True)
    async def redis(self, ctx, *args):
        try:
            output = await ctx.redis.execute(*args)
            await ctx.send(output or "None")
        except Exception as e:
            await ctx.send(e)


def setup(bot):
    bot.add_cog(Admin(bot))
