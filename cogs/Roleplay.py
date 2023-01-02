import discord
from discord.ext import commands

from cogs.utils.waifupics import get_waifu


class Roleplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def get_roleplay_embed(ctx, user_mentioned, type, category, action):
        title = f"{ctx.author.name} {action} "
        if user_mentioned is not None:  # PEP 8
            name = str(user_mentioned)
            size = len(name)
            title += name[: size - 5]
        embed = discord.Embed(title=title, color=0xEE615B)
        embed.set_image(url=await get_waifu(type, category))
        return embed

    @commands.command()
    async def cuddle(self, ctx, user_mentioned: discord.User = None):
        await ctx.send(
            embed=await self.get_roleplay_embed(
                ctx, user_mentioned, "sfw", "cuddle", "cuddles"
            )
        )

    @commands.command()
    async def hug(self, ctx, user_mentioned: discord.User = None):
        await ctx.send(
            embed=await self.get_roleplay_embed(
                ctx, user_mentioned, "sfw", "hug", "hugs"
            )
        )

    @commands.command()
    async def kiss(self, ctx, user_mentioned: discord.User = None):
        await ctx.send(
            embed=await self.get_roleplay_embed(
                ctx, user_mentioned, "sfw", "kiss", "kisses"
            )
        )

    @commands.command()
    async def lick(self, ctx, user_mentioned: discord.User = None):
        await ctx.send(
            embed=await self.get_roleplay_embed(
                ctx, user_mentioned, "sfw", "lick", "licks"
            )
        )

    @commands.command()
    async def pat(self, ctx, user_mentioned: discord.User = None):
        await ctx.send(
            embed=await self.get_roleplay_embed(
                ctx, user_mentioned, "sfw", "pat", "pats"
            )
        )

    @commands.command()
    async def bonk(self, ctx, user_mentioned: discord.User = None):
        await ctx.send(
            embed=await self.get_roleplay_embed(
                ctx, user_mentioned, "sfw", "bonk", "bonks"
            )
        )

    @commands.command()
    async def yeet(self, ctx, user_mentioned: discord.User = None):
        await ctx.send(
            embed=await self.get_roleplay_embed(
                ctx, user_mentioned, "sfw", "yeet", "yeets"
            )
        )

    @commands.command()
    async def wave(self, ctx, user_mentioned: discord.User = None):
        await ctx.send(
            embed=await self.get_roleplay_embed(
                ctx, user_mentioned, "sfw", "wave", "waves"
            )
        )

    @commands.command()
    async def highfive(self, ctx, user_mentioned: discord.User = None):
        await ctx.send(
            embed=await self.get_roleplay_embed(
                ctx, user_mentioned, "sfw", "highfive", "highfives"
            )
        )

    @commands.command()
    async def handhold(self, ctx, user_mentioned: discord.User = None):
        await ctx.send(
            embed=await self.get_roleplay_embed(
                ctx, user_mentioned, "sfw", "handhold", "handholds"
            )
        )

    @commands.command()
    async def bite(self, ctx, user_mentioned: discord.User = None):
        await ctx.send(
            embed=await self.get_roleplay_embed(
                ctx, user_mentioned, "sfw", "bite", "bites"
            )
        )

    @commands.command()
    async def glomp(self, ctx, user_mentioned: discord.User = None):
        await ctx.send(
            embed=await self.get_roleplay_embed(
                ctx, user_mentioned, "sfw", "glomp", "glomps"
            )
        )

    @commands.command()
    async def slap(self, ctx, user_mentioned: discord.User = None):
        await ctx.send(
            embed=await self.get_roleplay_embed(
                ctx, user_mentioned, "sfw", "slap", "slaps"
            )
        )

    # TODO: Add kill Abet bot easter egg (go offline status then back online and send some scary/taunting shit)
    @commands.command()
    async def kill(self, ctx, user_mentioned: discord.User = None):
        await ctx.send(
            embed=await self.get_roleplay_embed(
                ctx, user_mentioned, "sfw", "kill", "kills"
            )
        )

    @commands.command()
    async def kick(self, ctx, user_mentioned: discord.User = None):
        await ctx.send(
            embed=await self.get_roleplay_embed(
                ctx, user_mentioned, "sfw", "kick", "kicks"
            )
        )

    @commands.command()
    async def wink(self, ctx, user_mentioned: discord.User = None):
        await ctx.send(
            embed=await self.get_roleplay_embed(
                ctx, user_mentioned, "sfw", "wink", "winks at"
            )
        )

    @commands.command()
    async def poke(self, ctx, user_mentioned: discord.User = None):
        await ctx.send(
            embed=await self.get_roleplay_embed(
                ctx, user_mentioned, "sfw", "poke", "pokes"
            )
        )


async def setup(bot):
    await bot.add_cog(Roleplay(bot))
