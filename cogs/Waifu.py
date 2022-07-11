from discord.ext import commands


class Waifu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Note: Despite the same name with the slash cmd, they are not functionally equivalent.
    @commands.command()
    async def waifu(self, ctx):
        await ctx.send(await self.bot.get_waifu("sfw", "waifu"))

    @commands.command()
    async def neko(self, ctx):
        await ctx.send(await self.bot.get_waifu("sfw", "neko"))

    @commands.command()
    async def shinobu(self, ctx):
        await ctx.send(await self.bot.get_waifu("sfw", "shinobu"))

    @commands.command()
    async def megumin(self, ctx):
        await ctx.send(await self.bot.get_waifu("sfw", "megumin"))

    @commands.command()
    async def bully(self, ctx):
        await ctx.send(await self.bot.get_waifu("sfw", "bully"))

    @commands.command()
    async def cry(self, ctx):
        await ctx.send(await self.bot.get_waifu("sfw", "cry"))

    @commands.command()
    async def awoo(self, ctx):
        await ctx.send(await self.bot.get_waifu("sfw", "awoo"))

    @commands.command()
    async def smug(self, ctx):
        await ctx.send(await self.bot.get_waifu("sfw", "smug"))

    @commands.command()
    async def blush(self, ctx):
        await ctx.send(await self.bot.get_waifu("sfw", "blush"))

    @commands.command()
    async def smile(self, ctx):
        await ctx.send(await self.bot.get_waifu("sfw", "smile"))

    @commands.command()
    async def nom(self, ctx):
        await ctx.send(await self.bot.get_waifu("sfw", "nom"))

    @commands.command()
    async def happy(self, ctx):
        await ctx.send(await self.bot.get_waifu("sfw", "happy"))

    @commands.command()
    async def dance(self, ctx):
        await ctx.send(await self.bot.get_waifu("sfw", "dance"))

    @commands.command()
    async def cringe(self, ctx):
        await ctx.send(await self.bot.get_waifu("sfw", "cringe"))


async def setup(bot):
    await bot.add_cog(Waifu(bot))
