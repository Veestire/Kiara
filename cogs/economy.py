import asyncio
import random
from enum import Enum

import itertools
import collections

import discord
import logging
from discord.ext import commands

from cogs.utils.cooldowns import basic_cooldown
from .utils import fuzzy

log = logging.getLogger(__name__)


class Shop:
    __slots__ = ('id', 'name', 'description', 'icon', 'items')

    def __init__(self, *, id, name, description, icon=None, items=[]):
        self.id = id

    @classmethod
    def from_data(cls, data):
        self = cls.__new__(cls)

        self.id = data.get('id')
        self.name = data.get('name')
        self.description = data.get('description')
        self.icon = data.get('icon')
        self.items = []

        return self

    async def populate(self):
        pass

    def add_item(self, item):
        self.items += [item]

    def get(self, item):
        return discord.utils.get(self.items, name=item)

    def __name__(self):
        return self.name

    def __repr__(self):
        return f"<Shop id='{self.id}' name='{self.name}' items={len(self.items)}>"


class ShopItem:
    __slots__ = ('id', 'shop_id', 'name', 'type', 'cost', 'item_id', 'data', 'active')

    def __init__(self, id, shop_id, name, type, cost, item_id, data):
        self.shop_id = shop_id
        self.name = name
        self.type = type
        self.cost = cost
        self.item_id = item_id
        self.data = data

    @classmethod
    def from_data(cls, data):
        self = cls.__new__(cls)

        self.id = data.get('id')
        self.shop_id = data.get('shop_id')
        self.name = data.get('name')
        self.type = data.get('type')
        self.cost = data.get('cost')
        self.item_id = data.get('item_id')
        self.data = data.get('data')
        self.active = data.get('active')

        return self

    def get_role_id(self):
        if self.type != 'color_role':
            return None
        return self.data

    def __repr__(self):
        return f"<ShopItem name='{self.name} type={self.type} cost={self.cost} data={self.data}>"

    def get_name(self):
        if self.type == 'color_role':
            return f'<@&{self.data}>'
        else:
            return self.name

    def get_raw_text(self):
        ticks = ['<:redtick:526847326669504554>', '<:greentick:526847326812110933>']
        return f'{ticks[self.active]} `{self.id:03d}` {self.get_name()} | {self.cost}g'


class ShopItemType(Enum):
    BASIC = 1
    COLOR_ROLE = 2


class Economy:

    def __init__(self, bot):
        self.bot = bot
        self.profiles = bot.get_cog("Profiles")
        self._shops = []
        self.bot.loop.create_task(self.init_shop())

    async def init_shop(self):
        await self.bot.wait_until_ready()
        self._shops = []
        count = 0
        for shop_data in await self.bot.db.fetchdicts('SELECT * FROM shops WHERE active=1'):
            shop = Shop.from_data(shop_data)
            qry = 'SELECT * FROM shop_items WHERE shop_id=%s ORDER BY -sort_order DESC'
            for item_data in await self.bot.db.fetchdicts(qry, (shop.id,)):
                shop.add_item(ShopItem.from_data(item_data))
                count += 1
            self._shops.append(shop)
        log.info(f'Loaded {count} items from {len(self._shops)} shops')

    async def get_shops(self):
        if not self._shops:
            await self.init_shop()
        return self._shops

    def get_closest_item(self, item_name):
        items = fuzzy.finder(item_name, self.all_shop_items(), key=lambda t: t.name, lazy=False)
        return items[0] if items else None

    def all_shop_items(self, **data):
        for shop in self._shops:
            for item in shop.items:
                if all(getattr(item, key) == val for key, val in data.items() if val is not None):
                    yield item

    @commands.guild_only()
    @commands.group(invoke_without_command=True)
    async def shop(self, ctx, shop=None, extended=False):
        if ctx.invoked_subcommand:
            return

        shops = await self.get_shops()
        if not shops:
            return await ctx.send("Shop is empty atm.")

        if shop:
            try:
                shop = discord.utils.get(shops, name=shop) or discord.utils.get(shops, id=int(shop))
                if not shop:
                    shop = shops[0]
            except ValueError:
                pass

        else:
            shop = shops[0]

        emojis = ['❤', '💜', '🍉']

        # Fetch profile
        profile = await self.profiles.get_profile(ctx.author.id)

        # Fetch data
        owned_colors = await self.get_owned_colors(ctx.author.id)

        # Shop embed
        def get_shop_embed(shop_id):
            shop = discord.utils.get(shops, id=shop_id)
            shop_embed = discord.Embed(title=shop.name, description=shop.description+'\n\nBuy an item with `!buy [item]`.')
            for item in self.all_shop_items(shop_id=shop.id, active=True):
                if item.type == 'color_role':
                    item_name = f'**<@&{item.data}>**'
                    item_price = 'bought~' if item.data in owned_colors else f'{item.cost}g'
                else:
                    item_name = f'**{item.name}**'
                    item_price = f'{item.cost}g'
                shop_embed.add_field(name=f'\u200b', value=f'{item_name}\n{item_price}')

            shop_embed.set_footer(text=f"You have {profile.coins} gold")
            return shop_embed

        # Shop message
        shop_msg = await ctx.send(embed=get_shop_embed(shop.id))
        if not extended:
            return
        for em in emojis:
            await shop_msg.add_reaction(em)

        try:
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in emojis and reaction.message.id == shop_msg.id
            while True:
                r, u = await self.bot.wait_for('reaction_add', timeout=30, check=check)
                await shop_msg.remove_reaction(r, u)
                await shop_msg.edit(embed=get_shop_embed(emojis.index(str(r))+1))

        except asyncio.TimeoutError:
            await shop_msg.clear_reactions()

    @commands.has_role('Staff')
    @shop.command(name='reload', aliases=['update'])
    async def shop_reload(self, ctx):
        await self.init_shop()
        await ctx.send("Dun")

    @commands.has_role('Staff')
    @shop.command(name='raw', aliases=['rawdata'])
    async def shop_raw(self, ctx, shop_id: int = None):
        """Show items from a shop with their id etc"""
        pag = commands.Paginator('', '')
        if shop_id:
            pag.add_line(f'**Items in shop #{shop_id}**')
        else:
            pag.add_line('**Items in all shops**')
        items = self.all_shop_items(shop_id=shop_id)
        if items:
            for item in items:
                pag.add_line(item.get_raw_text())
        else:
            pag.add_line('Nothing')
        for page in pag.pages:
            await ctx.send(page)

    @commands.has_role('Staff')
    @shop.command(name='swap', aliases=['reorder'])
    async def shop_swap(self, ctx, item_one: int, item_two: int):
        """Swap the order of two items"""
        # qry = 'UPDATE shop_items s1, shop_items s2 ' \
        #       'SET s1.sort_order=s1.sort_order, s1.sort_order=s2.sort_order ' \
        #       'WHERE s1.id=s2.id AND s1.id=%s;'
        # await self.bot.db.execute(qry, (item_one, item_two))

    @commands.has_role('Staff')
    @shop.command(name='addcolor', aliases=['addrole'])
    async def shop_addcolor(self, ctx, shop_id: int, color: discord.Role, price: int = 50):
        qry = 'INSERT INTO shop_items (shop_id, type, name, cost, data) VALUES (%s,%s,%s,%s,%s)'
        await self.bot.db.execute(qry, (shop_id, 'color_role', color.name, price, color.id))
        await self.init_shop()
        await ctx.send(f'Added {color.mention} to shop #{shop_id}.')

    @commands.has_role('Staff')
    @shop.command(name='setprice', aliases=['setcost'])
    async def shop_setprice(self, ctx, item_id: int, price: int):
        item = discord.utils.get(self.all_shop_items(), id=item_id)
        if not item:
            return await ctx.send("Unknown item")
        qry = 'UPDATE shop_items SET cost=%s WHERE id=%s'
        await self.bot.db.execute(qry, (price, item_id))
        await self.init_shop()
        await ctx.send(f'Set the price of {item.name} to {price}.')

    @commands.has_role('Staff')
    @shop.command(name='toggle')
    async def shop_toggle(self, ctx, *item_ids: int):
        """Toggle an item's availabilty"""
        out = []
        for item_id in item_ids:
            item = discord.utils.get(self.all_shop_items(), id=item_id)
            qry = "UPDATE shop_items SET active = !active WHERE id=%s"
            await self.bot.db.execute(qry, (item_id,))
            out += [f'{item.name} is {"now" if item.active else "no longer"} for sale.']
        await ctx.send('\n'.join(out))
        await self.init_shop()

    @commands.has_role('Staff')
    @shop.command(name='toggleshop')
    async def shop_toggleshop(self, ctx, shop_id: int):
        """Toggle a whole shop"""
        qry = "UPDATE shops SET active = !active WHERE id=%s"
        await self.bot.db.execute(qry, (shop_id,))
        await ctx.send(f'Shop #{shop_id} is now {not item.active}')
        await self.init_shop()

    @commands.has_role('Staff')
    @shop.command(name='remove', aliases=['deleteitem'])
    async def shop_remove(self, ctx, shop_item_id: int):
        """Delete a whole shop"""
        qry = 'DELETE FROM shop_items WHERE id={shop_item_id}'
        await self.bot.db.execute(qry)
        await self.init_shop()
        await ctx.send(f'Deleted item with id #{shop_item_id}')

    @commands.guild_only()
    @commands.command(aliases=['buyitem', 'buycolor'], hidden=True)
    async def buy(self, ctx, *, item_name):
        """Buy an item from the shop"""
        item_name = item_name.lower()

        # Check if it matches an item
        item = self.get_closest_item(item_name)
        if not item:
            # Check if it matches a role
            role = fuzzy.finder(item_name, ctx.guild.roles, key=lambda t: t.name, lazy=False)
            if role:
                item = discord.utils.find(lambda x: x.data == role[0].id, self.all_shop_items())
                if not item:
                    return await ctx.send("This role isn't for sale.")
            else:
                return await ctx.send("I don't know which item you want to buy.")

        if item.type == 'color_role':
            if item.data in await self.get_owned_colors(ctx.author.id):
                return await ctx.send("You already own this color. Use `!swapcolor [color]` to change colors")

        if not item.active:
            return await ctx.send("This item isn't for sale at the moment.")

        # Handle transaction
        async with self.profiles.transaction(ctx.author.id, save=False) as profile:
            if profile.coins < item.cost:
                return await ctx.send("You don't have enough gold")
            profile.coins -= item.cost

            if item.type == 'color_role':
                role = discord.utils.get(ctx.guild.roles, id=item.data)
                if not role:
                    return await ctx.send("The role doesn't exist on the server")

                await self.bot.db.execute(f'INSERT INTO colors (user_id, color) VALUES ({ctx.author.id}, {item.data})')
                await self.swap_member_color(ctx.author, role)

                await profile.save()
                await ctx.send(f'Thanks for buying {item.get_name()}!')
            else:
                await ctx.send('Non color_role items not implemented')

    async def swap_member_color(self, member, role):
        topcolor = self.profiles.get_top_color(member.roles)
        if topcolor:
            await member.remove_roles(topcolor)

        await member.add_roles(role)


    @basic_cooldown(79200)
    @commands.guild_only()
    @commands.command(aliases=['daily'])
    async def dailies(self, ctx, *, receiver: discord.Member=None):
        """Claim your daily gold, or give it to someone else."""
        # Prevent lock freeze
        if receiver and receiver.id == ctx.author.id:
            receiver = None

        async with self.profiles.get_lock(ctx.author.id):
            profile = await self.profiles.get_profile(ctx.author.id, ('coins', 'level'))
            amount = int(random.randint(1, 5) * (1 + .2 * (profile.level//5)) * self.profiles.gold_rate)
            if receiver:
                async with self.profiles.get_lock(receiver.id):
                    profile2 = await self.profiles.get_profile(receiver.id, ('coins', 'level'))
                    profile2.coins += amount
                    await profile2.save(self.bot.db)
            else:
                profile.coins += amount
                await profile.save(self.bot.db)

        if receiver:
            await ctx.send(f"You gave <@{receiver.id}> {amount} gold as daily reward.")
        else:
            await ctx.send(f"You got {amount} gold as daily reward.")


    @dailies.error
    async def dailies_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await self.bot.redis.delete(f"cooldown:{ctx.author.id}:{ctx.command.qualified_name}")
        else:
            m, s = divmod(error.retry_after, 60)
            h, m = divmod(m, 60)

            t = f"{h:.0f} hour(s)" if h else f"{m:.0f} minute(s) and {s:.0f} second(s)" if m else f"{s:.0f} second(s)"
            msg = "You already collected your dailies.\nTry again in " + t

            await ctx.send(msg)

    async def get_owned_colors(self, user_id):
        owned = itertools.chain(*await self.bot.db.fetch(f'SELECT color FROM colors WHERE user_id={user_id}'))
        return list(owned)

    @commands.guild_only()
    @commands.command(aliases=['colors', 'setcolor', 'swapcolor', 'setcolour', 'swapcolour'])
    async def colours(self, ctx, *, colour=None):
        """Display your owned colors, or swap your color for a previously owned one."""
        owned = await self.get_owned_colors(ctx.author.id)
        if colour:
            role = discord.utils.find(lambda x: colour.lower() in x.name.lower(), ctx.guild.roles)
            if not role:
                return await ctx.send("This isn't a valid color")
            if role.id in owned:
                topcolor = self.profiles.get_top_color(ctx.author.roles)
                if topcolor:
                    await ctx.author.remove_roles(topcolor)
                await ctx.author.add_roles(role)
                await ctx.send(f"I'll swap your color to <@&{role.id}>")
        else:
            if owned:
                await ctx.send("You own the following colors:\n"+'\n'.join([f"<@&{role}>" for role in owned]))
            else:
                await ctx.send("You don't own any colors at the moment.")

    @commands.guild_only()
    @commands.command(aliases=['wallet', 'gold', 'money', 'coins'])
    async def balance(self, ctx, *, member: discord.Member = None):
        """Check how much gold you have"""
        if member is None:
            member = ctx.author

        profile = await self.profiles.get_profile(member.id, ('coins',))

        await ctx.send(embed=discord.Embed(title=f"{member.display_name} has {profile.coins} gold"))

    @commands.guild_only()
    @commands.command(aliases=['sendmoney', 'pay', 'tip'])
    async def givemoney(self, ctx, receiver: discord.Member = None, amount: int = 0):
        """Send some gold to someone"""
        if receiver is None:
            return await ctx.send("I don't know who you want to give money to.")
        if amount <= 0:
            return await ctx.send('Please provide an amount above 0.')

        sender = await self.profiles.get_profile(ctx.author.id, ('coins',))

        if sender.coins < amount:
            return await ctx.send("You don't have enough gold to transfer that much.")

        await ctx.send(embed=discord.Embed(description=f"Are you sure you want to send {amount}g to {receiver}? `y / n`"))
        response = await self.bot.wait_for('message', check=lambda m: m.author.id == ctx.author.id)

        if 'y' in response.content.lower():
            async with self.profiles.get_lock(ctx.author.id):
                sender = await self.profiles.get_profile(ctx.author.id, ('coins',))
                if sender.coins < amount:
                    return await ctx.send("You somehow don't have the funds to do this anymore.")
                sender.coins -= amount
                await sender.save(self.bot.db)
            async with self.profiles.get_lock(receiver.id):
                taker = await self.profiles.get_profile(receiver.id, ('coins',))
                taker.coins += amount
                await taker.save(self.bot.db)
            await ctx.send(embed=discord.Embed(description=f"You sent {receiver} {amount}g."))
        else:
            return await ctx.send("Transfer cancelled.")

    async def get_inventory(self, user_id):
        query = "SELECT item.* FROM inventory inv " \
                "INNER JOIN items item ON inv.item_id = item.id " \
                f"WHERE inv.user_id = %s"
        items = await self.bot.db.fetchdicts(query, (user_id,))
        return items

    @commands.command(aliases=['inv'])
    async def inventory(self, ctx, user:discord.User = None):
        items = await self.get_inventory(ctx.author.id)
        items = [f'<:bs:{item["icon"]}>' for item in items]
        await ctx.send(' '.join(items))

def setup(bot):
    bot.add_cog(Economy(bot))
