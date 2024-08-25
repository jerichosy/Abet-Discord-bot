from discord.ext import commands

from cogs.utils.waifupics import get_waifu


class Waifu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Note: Despite the same name with the slash cmd, they are not functionally equivalent.
    @commands.command()
    async def waifu(self, ctx):
        await ctx.send(await get_waifu("sfw", "waifu", self.bot.session))

    @commands.command()
    async def neko(self, ctx):
        await ctx.send(await get_waifu("sfw", "neko", self.bot.session))

    @commands.command()
    async def shinobu(self, ctx):
        await ctx.send(await get_waifu("sfw", "shinobu", self.bot.session))

    @commands.command()
    async def megumin(self, ctx):
        await ctx.send(await get_waifu("sfw", "megumin", self.bot.session))

    @commands.command()
    async def bully(self, ctx):
        await ctx.send(await get_waifu("sfw", "bully", self.bot.session))

    @commands.command()
    async def cry(self, ctx):
        await ctx.send(await get_waifu("sfw", "cry", self.bot.session))

    @commands.command()
    async def awoo(self, ctx):
        await ctx.send(await get_waifu("sfw", "awoo", self.bot.session))

    @commands.command()
    async def smug(self, ctx):
        await ctx.send(await get_waifu("sfw", "smug", self.bot.session))

    @commands.command()
    async def blush(self, ctx):
        await ctx.send(await get_waifu("sfw", "blush", self.bot.session))

    @commands.command()
    async def smile(self, ctx):
        await ctx.send(await get_waifu("sfw", "smile", self.bot.session))

    @commands.command()
    async def nom(self, ctx):
        await ctx.send(await get_waifu("sfw", "nom", self.bot.session))

    @commands.command()
    async def happy(self, ctx):
        await ctx.send(await get_waifu("sfw", "happy", self.bot.session))

    @commands.command()
    async def dance(self, ctx):
        await ctx.send(await get_waifu("sfw", "dance", self.bot.session))

    @commands.command()
    async def cringe(self, ctx):
        await ctx.send(await get_waifu("sfw", "cringe", self.bot.session))


async def setup(bot):
    await bot.add_cog(Waifu(bot))
