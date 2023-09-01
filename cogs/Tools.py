import io
import mimetypes
import os
import random
import uuid
from collections import Counter
from datetime import timedelta
from random import choices
from typing import Optional
from urllib.parse import urlparse

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from pdf2image import convert_from_bytes
from rembg import remove

from cogs.utils import responses_abet


class PDFFlags(commands.FlagConverter, prefix="--", delimiter=""):
    url: Optional[str]
    selection: Optional[str] = commands.flag(aliases=["sel"])


class Tools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.raw_string_menu = app_commands.ContextMenu(
            name="Get Message Content",
            callback=self.get_raw_string,
        )
        self.raw_embed_desc_menu = app_commands.ContextMenu(
            name="Get Embed Desc.",
            callback=self.get_raw_embed_desc_menu,
        )
        self.bot.tree.add_command(self.raw_string_menu)
        self.bot.tree.add_command(self.raw_embed_desc_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.raw_string_menu.name, type=self.raw_string_menu.type
        )
        self.bot.tree.remove_command(
            self.raw_embed_desc_menu.name, type=self.raw_embed_desc_menu.type
        )

    async def get_raw_string(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        if not message.content:
            emby = discord.Embed(
                description=f"🛑 That [message]({message.jump_url}) has no content"
            )
            return await interaction.response.send_message(embed=emby, ephemeral=True)

        emby = discord.Embed(
            description=f"Retrieved content of length {len(message.content)} from [message]({message.jump_url})"
        )
        await interaction.response.send_message(
            embed=emby,
            file=discord.File(io.BytesIO(message.content.encode()), "output.txt"),
            ephemeral=True,
        )

    async def get_raw_embed_desc_menu(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        if not message.embeds:
            emby = discord.Embed(
                description=f"🛑 That [message]({message.jump_url}) has no embeds"
            )
            return await interaction.response.send_message(embed=emby, ephemeral=True)

        emby = discord.Embed(
            description=f"Retrieved content of length {len(message.embeds[0].description)} from [message]({message.jump_url})"
        )
        await interaction.response.send_message(
            embed=emby,
            file=discord.File(
                io.BytesIO(message.embeds[0].description.encode()), "output.txt"
            ),
            ephemeral=True,
        )

    @staticmethod
    def coin_flip():
        population = ["Heads", "Tails"]
        weight = [0.1, 0.9]
        return (choices(population, weight))[0]

    @commands.hybrid_command(aliases=["coin"])
    async def coinflip(self, ctx):
        """Flip a sussy coin!"""
        await ctx.send(self.coin_flip())

    @commands.hybrid_command(aliases=["cointally"])
    @app_commands.describe(amount="The amount of sussy coins to flip")
    async def coinfliptally(self, ctx, amount: commands.Range[int, 2, 10000]):
        """Flip multiple sussy coins at once!"""
        heads_count = 0
        tails_count = 0

        for _ in range(amount):
            if self.coin_flip() == "Heads":
                heads_count += 1
            else:
                tails_count += 1

        await ctx.send(f"`Heads`: {heads_count}\n`Tails`: {tails_count}")

    @commands.hybrid_command()
    async def abet(self, ctx, *, question):
        """Magic 8 Ball: Abet Edition"""

        if ctx.guild.id == self.bot.HOME_GUILD.id:
            print("Home guild")
            await ctx.send(
                random.choice(
                    responses_abet.GLOBAL + responses_abet.OTHER + responses_abet.HOME
                )
            )
        elif ctx.guild.id == self.bot.OTHER_GUILD.id:
            print("Other guild")
            await ctx.send(random.choice(responses_abet.GLOBAL + responses_abet.OTHER))
        else:
            print("Global guild")
            await ctx.send(random.choice(responses_abet.GLOBAL))

    @commands.command()
    async def choose(self, ctx, *, choices):
        """Returns a random choice from the given words/phrases"""
        # choose_phrases = ctx.message.content[8:].split(", ")  # improper way
        choose_phrases = choices.split(", ")  # Split returns a list (square brackets)
        await ctx.send(random.choice(choose_phrases))

    @commands.command(aliases=["choosetally"])
    async def choosebestof(self, ctx, times: Optional[int], *, choices):
        choose_phrases = choices.split(", ")
        response = []

        if times is None:
            times = (len(choose_phrases) ** 2) + 1

        # if times > 10000:
        # response.append("Max of 10k only allowed!\n")
        times = min(10000, max(2, times))

        results = Counter(random.choice(choose_phrases) for _ in range(times))
        if len(results) > 10:
            response.append("Only showing top 10 results...")
        for index, (elem, count) in enumerate(results.most_common(10), start=1):
            response.append(
                f'{index}. {elem} ({count} {"time" if count == 1 else "times"}, {count/times:.2%})'
            )

        await ctx.send("\n".join(response))

    @commands.hybrid_command(aliases=["wait", "anime"])
    async def whatanime(
        self, ctx, url=None, attachment: Optional[discord.Attachment] = None
    ):
        """What Anime Is This"""

        if url is None and len(ctx.message.attachments) == 0:
            return await ctx.send("Please attach an image / provide a link or URL")

        url = ctx.message.attachments[0].url if ctx.message.attachments else url

        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.trace.moe/search?cutBorders&anilistInfo&url={url}"
                ) as resp:
                    json_data = await resp.json()

                    if json_data["error"]:
                        return await ctx.send(json_data["error"])

                    # Get titles, filename, episode & timestamp, and similarity percentage

                    native = (
                        ""
                        if json_data["result"][0]["anilist"]["title"]["native"] is None
                        else f"**{json_data['result'][0]['anilist']['title']['native']}**\n"
                    )
                    romaji = (
                        ""
                        if json_data["result"][0]["anilist"]["title"]["romaji"] is None
                        else f"**{json_data['result'][0]['anilist']['title']['romaji']}**\n"
                    )
                    english = (
                        ""
                        if json_data["result"][0]["anilist"]["title"]["english"] is None
                        else f"**{json_data['result'][0]['anilist']['title']['english']}**\n"
                    )

                    file_name = json_data["result"][0]["filename"]

                    # Get episode number if present
                    timestamp = ""
                    if json_data["result"][0]["episode"] is not None:
                        timestamp = f"Episode {json_data['result'][0]['episode']} | "
                    # Then concat timestamp regardless if there was an episode no. or not
                    timestamp += str(
                        timedelta(seconds=int(json_data["result"][0]["from"]))
                    )

                    similarity = json_data["result"][0]["similarity"]

                    # Preview related stuff
                    video_url = json_data["result"][0]["video"]
                    if json_data["result"][0]["anilist"]["isAdult"]:
                        spoiler = True
                        warning = "[NSFW]"
                    else:
                        spoiler = False
                        warning = ""

                async with session.get(video_url) as resp:
                    data = None
                    if resp.status == 200:
                        data = io.BytesIO(await resp.read())
                    else:
                        warning = "Could not download preview..."

                await ctx.reply(
                    f"{native}{romaji}{english}``{file_name}``\n{timestamp}\n{'{:.1f}'.format(similarity * 100)}% similarity\n\n{warning}",
                    file=discord.File(fp=data, filename="preview.mp4", spoiler=spoiler)
                    if data
                    else None,
                )

    @commands.hybrid_command(
        aliases=["sauce", "source", "getsource", "artsource", "getartsource"]
    )
    async def saucenao(
        self, ctx, url=None, attachment: Optional[discord.Attachment] = None
    ):
        """SauceNAO Reverse Image Search (manga, doujinshi, fanart, anime, etc.)"""

        if url is None and len(ctx.message.attachments) == 0:
            return await ctx.send("Please attach an image / provide a link or URL")

        url = ctx.message.attachments[0].url if ctx.message.attachments else url

        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://saucenao.com/search.php?db=999&output_type=2&numres=1&url={url}&api_key={os.getenv('SAUCENAO_TOKEN')}"
                ) as r:
                    json_data = await r.json()
                    # print(json_data)

                    # SauceNAO API documentation: https://saucenao.com/user.php?page=search-api

                    # error checking
                    if r.status != 200 or json_data["header"]["status"] != 0:
                        if json_data["header"]["status"] < 0:
                            if json_data["header"]["status"] == -2:
                                return await ctx.send(
                                    "Search Rate Too High. Your IP has exceeded the basic account type's rate limit of 6 searches every 30 seconds."
                                )
                            else:
                                return await ctx.send(
                                    "Client side error (bad image, out of searches, etc)"
                                )
                        else:
                            return await ctx.send(
                                "Server side error (failed descriptor gen, failed query, etc). Please try again!"
                            )

                    # if successful
                    def get_json_field(prefix, parameter):
                        try:
                            field = (
                                ""
                                if not json_data["results"][0]["data"][parameter]
                                else f"{prefix}{json_data['results'][0]['data'][parameter]}\n"
                            )
                            # print(json_data['results'][0]['data'][parameter])
                        except KeyError:
                            field = ""

                        return field

                    source = get_json_field("**Sauce:** ", "source")
                    if source == "":
                        source = f"**Sauce:** {json_data['results'][0]['data']['ext_urls'][0]}\n"
                    # to handle Pixiv urls like
                    # https://i.pximg.net/img-original/img/2021/07/28/07/50/29/91550773 with https://cdn.discordapp.com/attachments/870095545992101958/947297823945293834/lASQNdS.jpg or
                    # http://i2.pixiv.net/img-original/img/2016/01/16/01/19/56/54734137 with https://cdn.discordapp.com/attachments/870095545992101958/947296081354588211/54734137_p0_master1200.png
                    elif "/img-original/img/" in source:
                        source = f"**Sauce:** https://pixiv.net/en/artworks/{source[len(source) - 9 : len(source)]}"
                    part = get_json_field("**Part:** ", "part")
                    characters = get_json_field("**Character(s):** ", "characters")
                    similarity = f"**Similarity:** {float(json_data['results'][0]['header']['similarity'])}%"

                    danbooru = get_json_field("Danbooru ID: ", "danbooru_id")
                    yandere = get_json_field("Yandere ID: ", "yandere_id")
                    gelbooru = get_json_field("Gelbooru ID: ", "gelbooru_id")

                    separator = (
                        ""
                        if danbooru == "" and yandere == "" and gelbooru == ""
                        else "\n------------------------\n"
                    )

                    await ctx.reply(
                        f"{source}{part}{characters}{similarity}{separator}{danbooru}{yandere}{gelbooru}"
                    )

    # FIXME: This is blocking
    @commands.hybrid_command()
    # "attachment" is not accessed as the attachment is already retrievable by message.attachments[0].url
    # and to maintain compatibility with traditional cmd usage. But the arg. is necessary to indicate as a slash cmd arg. for the user
    async def pdf(
        self,
        ctx,
        attachment: Optional[discord.Attachment],
        *,
        flags: PDFFlags,
    ):
        """Post the uploaded PDF as a series of images"""

        if flags.url is None and len(ctx.message.attachments) == 0:
            return await ctx.send("Please attach a PDF / provide a link or URL")

        url = ctx.message.attachments[0].url if ctx.message.attachments else flags.url
        print(url)

        def parse_selected_pages(input_str, last_page):
            pages = []

            for part in input_str.split(","):
                # Remove whitespaces
                part = part.strip()

                # Check if part contains a range (e.g. 4-6)
                if "-" in part:
                    start, end = part.split("-")
                    pages.extend(range(int(start), int(end) + 1))
                else:
                    pages.append(int(part))

            # Remove duplicates in selection ranges
            pages = list(dict.fromkeys(pages))
            # Filter out less than 1 and beyond last page selection ranges
            pages = [page for page in pages if (page > 0) and (page <= last_page)]
            # Sort, then return
            return sorted(pages)

        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.headers.get("Content-Type") != "application/pdf":
                        return await ctx.send(
                            "ERROR: Given file / link or URL is not a PDF file"
                        )

                    images = convert_from_bytes(await resp.read())

                    image_list = []
                    for image in images:
                        image_bytes = io.BytesIO()
                        image.save(image_bytes, "JPEG")
                        image_bytes.seek(0)
                        image_list.append(
                            discord.File(image_bytes, f"{uuid.uuid4()}.jpg")
                        )

                    if flags.selection:
                        try:
                            selected_pages = parse_selected_pages(
                                flags.selection, len(image_list)
                            )
                            print(selected_pages)
                        except ValueError:
                            return await ctx.reply("🛑 Error parsing selection range")
                        if len(selected_pages) == 0:
                            return await ctx.reply("🛑 Invalid selection range")

                        # Get selected pages
                        image_list = [
                            # image_list[min(max(i, 1) - 1, len(image_list) - 1)]
                            image_list[i - 1]
                            for i in selected_pages
                        ]

                    chunks = [
                        image_list[x : x + 10] for x in range(0, len(image_list), 10)
                    ]

                    for idx, chunk in enumerate(chunks):
                        page_increment = 10 * idx
                        low = page_increment + 1
                        high = (len(chunk) - 1) + low

                        source_page_cnt = ""  # ! This is not currently used.
                        # if start != 1 or end:
                        #     low_source = page_increment + start
                        #     high_source = (len(chunk) - 1) + low_source
                        #     source_page_cnt = f"({low_source}-{high_source})"

                        sender = ctx.reply if idx == 0 else ctx.channel.send

                        await sender(
                            f"Page {low}-{high}/{len(image_list)} {source_page_cnt}",
                            files=chunk,
                        )

    @commands.hybrid_command(aliases=["rembg", "rmbg", "bgremove"])
    async def removebg(
        self, ctx, url=None, attachment: Optional[discord.Attachment] = None
    ):
        """Remove background from an image"""

        if url is None and len(ctx.message.attachments) == 0:
            return await ctx.send("Please attach an image / provide a link or URL")

        url = ctx.message.attachments[0].url if ctx.message.attachments else url
        # ? Should we add support for multiple images at once?

        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    print(resp.status)
                    print(resp.headers.get("Content-Type"))
                    # I think PIL in rembg code should handle errors related to non-image urls

                    output = remove(await resp.read())
                    await ctx.send(
                        file=discord.File(io.BytesIO(output), f"{uuid.uuid4()}.png")
                    )

    @commands.hybrid_command()
    @app_commands.describe(location="Check the weather at the specified location")
    async def weather(self, ctx, location: str = "Pasig"):
        """Check the weather!"""

        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://wttr.in/{location}?0T") as resp:
                    if (
                        await resp.text() == ""
                        or await resp.text()
                        == "Follow @igor_chubin for wttr.in updates"
                    ):
                        return await ctx.send(
                            "The weather service is having problems. Please try again later."
                        )
                    # print(await resp.text())
                    await ctx.send(f"```{await resp.text()}```")

    @app_commands.command()
    @app_commands.describe(url="The direct link to the file")
    async def repost(self, interaction: discord.Interaction, url: str):
        """Reposts the file located at the given URL (subject to 25MB non-boosted server limitation)"""

        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url
            ) as resp:  # TODO: Currently does not validate URLs
                print(
                    f"Reposter HTTP status: {resp.status}, Content length: {resp.content_length}"
                )
                if resp.status == 200:
                    file_bytes = io.BytesIO(await resp.read())
                    # file_format = mimetypes.guess_extension(
                    #     resp.headers.get("Content-Type")
                    # )
                    filename = os.path.basename(urlparse(url).path)
                    print("Reposter filename:", filename)
                    if not filename:
                        # if no filename, the upload will fail raising discord.HTTPException
                        # fall back to using uuid and mimetypes
                        filename = f"{uuid.uuid4()}{mimetypes.guess_extension(resp.headers.get('Content-Type'))}"
                        print("Adjusted filename:", filename)
                    try:
                        await interaction.followup.send(
                            file=discord.File(
                                file_bytes,
                                f"{filename}",
                            ),
                        )
                    except discord.HTTPException as e:
                        await interaction.followup.send(
                            content=f"HTTPException: {e}", ephemeral=True
                        )
                else:
                    await interaction.followup.send(
                        content="Did not return 200 status code", ephemeral=True
                    )


async def setup(bot):
    await bot.add_cog(Tools(bot))
