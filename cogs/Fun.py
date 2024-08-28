import asyncio
import os
import random
from io import BytesIO
from typing import List, Literal

import aiohttp
import discord
from discord import app_commands
from discord.app_commands import Group
from discord.ext import commands

from .utils.context import Context

WAIFU_IM_API_HEADERS = {"Accept-Version": "v6"}


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Don't make this into an embed
    @commands.hybrid_command(aliases=["fuckcarl"])
    async def carl(self, ctx):
        """Dish Carl"""
        await ctx.send("https://cdn.discordapp.com/attachments/731542246951747594/905830644607758416/abet_bot.png")

    async def get_json_quote(self, url):
        async with self.bot.session.get(url) as resp:
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
            json_data = await self.get_json_quote("https://api.tronalddump.io/random/quote")
            quote = json_data["value"] + " -Donald Trump"
            await ctx.send(quote, suppress_embeds=True)
        else:
            async with ctx.session.get("https://api.tronalddump.io/random/meme") as r:
                data = BytesIO(await r.read())
                await ctx.send(file=discord.File(data, "tronalddump.jpeg"))

    @commands.hybrid_command(aliases=["meow"])
    async def cat(self, ctx: Context):
        """Gives you a random cat."""
        async with ctx.session.get("https://api.thecatapi.com/v1/images/search") as resp:
            if resp.status != 200:
                return await ctx.send("No cat found :(")
            js = await resp.json()
            await ctx.send(embed=discord.Embed(title="Random Cat").set_image(url=js[0]["url"]))

    @commands.hybrid_command()
    async def dog(self, ctx: Context):
        """Gives you a random dog."""
        async with ctx.session.get("https://random.dog/woof") as resp:
            if resp.status != 200:
                return await ctx.send("No dog found :(")

            filename = await resp.text()
            url = f"https://random.dog/{filename}"
            filesize = ctx.guild.filesize_limit if ctx.guild else 8388608
            if filename.endswith((".mp4", ".webm")):
                async with ctx.typing():
                    async with ctx.session.get(url) as other:
                        if other.status != 200:
                            return await ctx.send("Could not download dog video :(")

                        if int(other.headers["Content-Length"]) >= filesize:
                            return await ctx.send(f"Video was too big to upload... See it here: {url} instead.")

                        fp = BytesIO(await other.read())
                        await ctx.send(file=discord.File(fp, filename=filename))
            else:
                await ctx.send(embed=discord.Embed(title="Random Dog").set_image(url=url))

    @commands.hybrid_command()
    async def uselessfact(self, ctx):
        """Not sure why I added a totally useless feature"""
        async with ctx.session.get("https://uselessfacts.jsph.pl/api/v2/facts/random?language=en") as r:
            await ctx.send((await r.json())["text"])

    # Lifted from https://github.com/Rapptz/discord.py/blob/master/examples/guessing_game.py
    @commands.command(aliases=["game"])
    async def guess(self, ctx):
        await ctx.send("Guess a number between 1 and 10.")

        def is_correct(m):
            return m.channel == ctx.channel and m.author == ctx.author and m.content.isdigit()

        answer = random.randint(1, 10)

        try:
            guess = await self.bot.wait_for("message", check=is_correct, timeout=5.0)
        except asyncio.TimeoutError:
            return await ctx.send(f"Sorry, you took too long it was {answer}.")

        if int(guess.content) == answer:
            await ctx.send("You are right!")
        else:
            await ctx.send(f"Oops. It is actually {answer}.")

    # TODO: aliases=["wai", "waikeili", "waikei"]
    # TODO: make this work as hybrid cmds
    waikei_group = Group(name="waikei", description="Waikei commands")

    @waikei_group.command(name="stop-generating")
    async def stop_generating(self, interaction):
        async with self.bot.session.post(f"{os.getenv('YT_DLP_MICROSERVICE')}/waikei-pretrained/stop-generating") as resp:
            # Print status line
            msg = [f"HTTP/{resp.version.major}.{resp.version.minor} {resp.status} {resp.reason}"]

            # Print headers
            for key, value in resp.headers.items():
                msg.append(f"{key}: {value}")

            # Print content
            msg.append(f"\n{await resp.text()}")

            await interaction.response.send_message("\n".join(msg))

    async def get_waifu_im_embed(self, type, category):
        type = "false" if type == "sfw" else "true"
        url_string = f"https://api.waifu.im/search/?included_tags={category}&is_nsfw={type}"

        async with self.bot.session.get(url_string, headers=WAIFU_IM_API_HEADERS) as resp:
            print(f"Waifu.im: {resp.status}")
            json_data = await resp.json()
            if resp.status in {200, 201}:
                # embed = discord.Embed(color=0xffc0cb)
                embed = discord.Embed(
                    color=int(
                        f"0x{json_data['images'][0]['dominant_color'].lstrip('#')}",
                        0,
                    )
                )
                embed.set_image(url=json_data["images"][0]["url"])

                source = json_data["images"][0]["source"]

                # print(json_data)

            else:
                # Print error
                print(json_data["message"])

        return source, embed

    waifu_group = Group(name="waifu", description="Waifu.im slash commands")

    @waifu_group.command()
    @app_commands.describe(is_ephemeral='If "Yes", the image will only be visible to you')
    async def sfw(
        self,
        interaction: discord.Interaction,
        tag: str,
        is_ephemeral: Literal["No", "Yes"] = "No",
    ) -> None:
        """random sfw Waifu images"""
        if tag in self.waifu_im_tags["nsfw"]:
            return await interaction.response.send_message(
                "You are requesting NSFW tags in an SFW command. Please use /waifu nsfw",
                ephemeral=True,
            )

        text, embed = await self.get_waifu_im_embed("sfw", tag)
        await interaction.response.send_message(
            content=text,
            embed=embed,
            ephemeral=True if is_ephemeral == "Yes" else False,
        )

    @waifu_group.command()
    @app_commands.describe(is_ephemeral='If "Yes", the image will only be visible to you')
    async def nsfw(
        self,
        interaction: discord.Interaction,
        tag: str,
        is_ephemeral: Literal["No", "Yes"] = "No",
    ) -> None:
        """random nsfw Waifu images"""
        if tag in self.waifu_im_tags["versatile"]:
            return await interaction.response.send_message(
                "You are requesting SFW tags in an NSFW command. Please use /waifu sfw",
                ephemeral=True,
            )
        if not interaction.channel.is_nsfw() and is_ephemeral == "No":
            return await interaction.response.send_message(
                "You requested a visible NSFW image in a non-NSFW channel! Please use in the appropriate channel(s).",
                ephemeral=True,
            )

        text, embed = await self.get_waifu_im_embed("nsfw", tag)
        await interaction.response.send_message(
            content=text,
            embed=embed,
            ephemeral=True if is_ephemeral == "Yes" else False,
        )

    async def refresh_waifu_im_tags(self):
        # Populate the waifu_im_tags list (for waifu slash cmd)
        async with self.bot.session.get("https://api.waifu.im/tags", headers=WAIFU_IM_API_HEADERS) as r:
            print(f"Waifu.im tags query status code: {r.status}")
            if r.status == 200:
                return await r.json()

    @sfw.autocomplete("tag")
    async def sfw_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        if not hasattr(self, "waifu_im_tags"):
            self.waifu_im_tags = await self.refresh_waifu_im_tags()

        return [
            app_commands.Choice(name=waifu_im_tag, value=waifu_im_tag)
            for waifu_im_tag in self.waifu_im_tags["versatile"]
            if current.lower() in waifu_im_tag.lower()
        ]

    @nsfw.autocomplete("tag")
    async def nsfw_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        if not hasattr(self, "waifu_im_tags"):
            self.waifu_im_tags = await self.refresh_waifu_im_tags()

        return [
            app_commands.Choice(name=waifu_im_tag, value=waifu_im_tag)
            for waifu_im_tag in self.waifu_im_tags["nsfw"]
            if current.lower() in waifu_im_tag.lower()
        ]


async def setup(bot):
    await bot.add_cog(Fun(bot))
