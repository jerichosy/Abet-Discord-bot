from discord.ext import commands


class NSFW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_nsfw()
    async def hentai(self, ctx):
        """( ͡° ͜ʖ ͡°)"""
        await ctx.send(await self.bot.get_waifu("nsfw", "waifu"))

    @commands.command()
    @commands.is_nsfw()
    async def nekonsfw(self, ctx):
        await ctx.send(await self.bot.get_waifu("nsfw", "neko"))

    @commands.command()
    @commands.is_nsfw()
    async def trap(self, ctx):
        await ctx.send(await self.bot.get_waifu("nsfw", "trap"))

    @commands.command()
    @commands.is_nsfw()
    async def blowjob(self, ctx):
        await ctx.send(await self.bot.get_waifu("nsfw", "blowjob"))

    @commands.command()
    @commands.is_nsfw()
    async def ass(self, ctx):
        text, embed = await self.bot.get_waifu_im_embed("nsfw", "ass")
        await ctx.send(text, embed=embed)

    @commands.command()
    @commands.is_nsfw()
    async def ero(self, ctx):
        text, embed = await self.bot.get_waifu_im_embed("nsfw", "ero")
        await ctx.send(text, embed=embed)

    @commands.command()
    @commands.is_nsfw()
    async def hentai2(self, ctx):
        text, embed = await self.bot.get_waifu_im_embed("nsfw", "hentai")
        await ctx.send(text, embed=embed)

    @commands.command()
    @commands.is_nsfw()
    async def milf(self, ctx):
        text, embed = await self.bot.get_waifu_im_embed("nsfw", "milf")
        await ctx.send(text, embed=embed)

    @commands.command()
    @commands.is_nsfw()
    async def oral(self, ctx):
        text, embed = await self.bot.get_waifu_im_embed("nsfw", "oral")
        await ctx.send(text, embed=embed)

    @commands.command()
    @commands.is_nsfw()
    async def paizuri(self, ctx):
        text, embed = await self.bot.get_waifu_im_embed("nsfw", "paizuri")
        await ctx.send(text, embed=embed)

    @commands.command()
    @commands.is_nsfw()
    async def ecchi(self, ctx):
        text, embed = await self.bot.get_waifu_im_embed("nsfw", "ecchi")
        await ctx.send(text, embed=embed)


async def setup(bot):
    await bot.add_cog(NSFW(bot))
