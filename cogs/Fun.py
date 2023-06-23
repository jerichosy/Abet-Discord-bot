import asyncio
import io
import random
from typing import List, Literal

import aiohttp
import discord
from discord import app_commands
from discord.app_commands import Group
from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Don't make this into an embed
    @commands.hybrid_command(aliases=["fuckcarl"])
    async def carl(self, ctx):
        """Dish Carl"""
        await ctx.send(
            "https://cdn.discordapp.com/attachments/731542246951747594/905830644607758416/abet_bot.png"
        )

    @staticmethod
    async def get_json_quote(url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                json_data = await resp.json()
        return json_data

    @commands.hybrid_command(aliases=["inspo", "inspiration"])
    async def inspire(self, ctx):
        """random inspirational quote"""
        json_data = await self.get_json_quote("https://zenquotes.io/api/random")
        quote = json_data[0]["q"] + " -" + json_data[0]["a"]
        await ctx.send(quote)

    @commands.hybrid_command(aliases=["kanyewest", "ye"])
    async def kanye(self, ctx):
        """random Kanye West quotes (Kanye as a Service)"""
        json_data = await self.get_json_quote("https://api.kanye.rest/")
        quote = json_data["quote"] + " -Kanye West"
        await ctx.send(quote)

    @commands.hybrid_command()
    async def trump(
        self,
        ctx,
        in_image_form: Literal["No", "Yes"] = "No",
    ):
        """random dumbest things Donald Trump has ever said"""

        if in_image_form == "No":
            json_data = await self.get_json_quote(
                "https://api.tronalddump.io/random/quote"
            )
            quote = json_data["value"] + " -Donald Trump"
            await ctx.send(quote, suppress_embeds=True)
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.tronalddump.io/random/meme") as r:
                    data = io.BytesIO(await r.read())
                    await ctx.send(file=discord.File(data, "tronalddump.jpeg"))

    @commands.hybrid_command(aliases=["meow"])
    async def cat(self, ctx):
        """random cat pics"""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        ) as session:
            async with session.get("http://aws.random.cat/meow") as r:
                js = await r.json()
                await ctx.send(js["file"])

    @commands.hybrid_command()
    async def uselessfact(self, ctx):
        """Not sure why I added a totally useless feature"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en"
            ) as r:
                await ctx.send((await r.json())["text"])

    # Lifted from https://github.com/Rapptz/discord.py/blob/master/examples/guessing_game.py
    @commands.command(aliases=["game"])
    async def guess(self, ctx):
        await ctx.send("Guess a number between 1 and 10.")

        def is_correct(m):
            return m.author == ctx.author and m.content.isdigit()

        answer = random.randint(1, 10)

        try:
            guess = await self.bot.wait_for("message", check=is_correct, timeout=5.0)
        except asyncio.TimeoutError:
            return await ctx.send(f"Sorry, you took too long it was {answer}.")

        if int(guess.content) == answer:
            await ctx.send("You are right!")
        else:
            await ctx.send(f"Oops. It is actually {answer}.")

    waifu_group = Group(name="waifu", description="Waifu.im slash commands")

    @waifu_group.command()
    @app_commands.describe(
        is_ephemeral='If "Yes", the image will only be visible to you'
    )
    async def sfw(
        self,
        interaction: discord.Interaction,
        tag: str,
        is_ephemeral: Literal["No", "Yes"] = "No",
    ) -> None:
        """random sfw Waifu images"""
        if tag in waifu_im_tags["nsfw"]:
            return await interaction.response.send_message(
                "You are requesting NSFW tags in an SFW command. Please use /waifu nsfw",
                ephemeral=True,
            )

        text, embed = await self.bot.get_waifu_im_embed("sfw", tag)
        await interaction.response.send_message(
            content=text,
            embed=embed,
            ephemeral=True if is_ephemeral == "Yes" else False,
        )

    @waifu_group.command()
    @app_commands.describe(
        is_ephemeral='If "Yes", the image will only be visible to you'
    )
    async def nsfw(
        self,
        interaction: discord.Interaction,
        tag: str,
        is_ephemeral: Literal["No", "Yes"] = "No",
    ) -> None:
        """random nsfw Waifu images"""
        if tag in waifu_im_tags["versatile"]:
            return await interaction.response.send_message(
                "You are requesting SFW tags in an NSFW command. Please use /waifu sfw",
                ephemeral=True,
            )
        if not interaction.channel.is_nsfw() and is_ephemeral == "No":
            return await interaction.response.send_message(
                "You requested a visible NSFW image in a non-NSFW channel! Please use in the appropriate channel(s).",
                ephemeral=True,
            )

        text, embed = await self.bot.get_waifu_im_embed("nsfw", tag)
        await interaction.response.send_message(
            content=text,
            embed=embed,
            ephemeral=True if is_ephemeral == "Yes" else False,
        )

    @sfw.autocomplete("tag")
    async def sfw_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=waifu_im_tag, value=waifu_im_tag)
            for waifu_im_tag in waifu_im_tags["versatile"]
            if current.lower() in waifu_im_tag.lower()
        ]

    @nsfw.autocomplete("tag")
    async def nsfw_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=waifu_im_tag, value=waifu_im_tag)
            for waifu_im_tag in waifu_im_tags["nsfw"]
            if current.lower() in waifu_im_tag.lower()
        ]


async def setup(bot):
    # Populate the waifu_im_tags list (for waifu slash cmd)
    async with aiohttp.ClientSession() as cs:
        async with cs.get("https://api.waifu.im/tags") as r:
            print(f"Waifu.im endpoint: {r.status}")
            if r.status == 200:
                global waifu_im_tags
                waifu_im_tags = await r.json()

    await bot.add_cog(Fun(bot))
