import asyncio
import mimetypes
import os
import random
import uuid
from collections import Counter
from datetime import timedelta
from io import BytesIO
from random import choices
from typing import Optional
from urllib.parse import quote_plus, urlparse

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from pdf2image import convert_from_bytes
from rembg import remove

from cogs.utils import responses_abet
from cogs.utils.character_limits import MessageLimit, truncate
from cogs.utils.context import Context
from models.db import TagsManager


class PDFFlags(commands.FlagConverter, prefix="--", delimiter=""):
    url: Optional[str] = commands.flag(aliases=["link"])
    selection: Optional[str] = commands.flag(aliases=["sel", "page"])


class Tools(commands.Cog):
    def __init__(self, bot, tags_manager: TagsManager):
        self.bot = bot
        self.tags_manager = tags_manager
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
        self.bot.tree.remove_command(self.raw_string_menu.name, type=self.raw_string_menu.type)
        self.bot.tree.remove_command(self.raw_embed_desc_menu.name, type=self.raw_embed_desc_menu.type)

    async def get_raw_string(self, interaction: discord.Interaction, message: discord.Message):
        if not message.content:
            emby = discord.Embed(description=f"🛑 That [message]({message.jump_url}) has no content")
            return await interaction.response.send_message(embed=emby, ephemeral=True)

        emby = discord.Embed(
            description=f"Retrieved content of length {len(message.content)} from [message]({message.jump_url})"
        )
        await interaction.response.send_message(
            embed=emby,
            file=discord.File(BytesIO(message.content.encode()), "output.txt"),
            ephemeral=True,
        )

    async def get_raw_embed_desc_menu(self, interaction: discord.Interaction, message: discord.Message):
        if not message.embeds:
            emby = discord.Embed(description=f"🛑 That [message]({message.jump_url}) has no embeds")
            return await interaction.response.send_message(embed=emby, ephemeral=True)

        emby = discord.Embed(
            description=f"Retrieved content of length {len(message.embeds[0].description)} from [message]({message.jump_url})"
        )
        await interaction.response.send_message(
            embed=emby,
            file=discord.File(BytesIO(message.embeds[0].description.encode()), "output.txt"),
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
            await ctx.send(random.choice(responses_abet.GLOBAL + responses_abet.OTHER + responses_abet.HOME))
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
            response.append(f'{index}. {elem} ({count} {"time" if count == 1 else "times"}, {count/times:.2%})')

        await ctx.send("\n".join(response))

    @commands.hybrid_command(aliases=["wait", "anime"])
    async def whatanime(self, ctx, url=None, attachment: Optional[discord.Attachment] = None):
        """What Anime Is This"""

        if url is None and not ctx.message.attachments:
            return await ctx.send("Please attach an image / provide a link or URL")

        url = ctx.message.attachments[0].url if ctx.message.attachments else url

        async with ctx.typing():
            async with ctx.session.get(
                "https://api.trace.moe/search?cutBorders&anilistInfo&url={}".format(quote_plus(url))
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
                timestamp += str(timedelta(seconds=int(json_data["result"][0]["from"])))

                similarity = json_data["result"][0]["similarity"]

                # Preview related stuff
                video_url = json_data["result"][0]["video"]
                if json_data["result"][0]["anilist"]["isAdult"]:
                    spoiler = True
                    warning = "[NSFW]"
                else:
                    spoiler = False
                    warning = ""

            async with ctx.session.get(video_url) as resp:
                data = None
                if resp.status == 200:
                    data = BytesIO(await resp.read())
                else:
                    warning = "Could not download preview..."

            await ctx.reply(
                f"{native}{romaji}{english}``{file_name}``\n{timestamp}\n{'{:.1f}'.format(similarity * 100)}% similarity\n\n{warning}",
                file=(discord.File(fp=data, filename="preview.mp4", spoiler=spoiler) if data else None),
            )

    @commands.hybrid_command(aliases=["sauce", "source", "getsource", "artsource", "getartsource"])
    async def saucenao(self, ctx, url=None, attachment: Optional[discord.Attachment] = None):
        """SauceNAO Reverse Image Search (manga, doujinshi, fanart, anime, etc.)"""

        if url is None and not ctx.message.attachments:
            return await ctx.send("Please attach an image / provide a link or URL")

        url = ctx.message.attachments[0].url if ctx.message.attachments else url

        async with ctx.typing():
            params = {
                "db": 999,
                "output_type": 2,
                "numres": 1,
                "url": url,
                "api_key": os.getenv("SAUCENAO_TOKEN"),
            }
            async with ctx.session.get("https://saucenao.com/search.php", params=params) as r:
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
                            return await ctx.send("Client side error (bad image, out of searches, etc)")
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

                separator = "" if danbooru == "" and yandere == "" and gelbooru == "" else "\n------------------------\n"

                await ctx.reply(f"{source}{part}{characters}{similarity}{separator}{danbooru}{yandere}{gelbooru}")

    @commands.hybrid_command()
    @commands.max_concurrency(number=1, per=commands.BucketType.default, wait=True)
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

        if flags.url is None and not ctx.message.attachments:
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

        async def convert_pdf_to_images(data):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.bot.executor, convert_from_bytes, data)

        async with ctx.typing():
            # Note: Some links have dynamic granular security measures: https://caap.gov.ph/wp-content/uploads/2024/05/MC-010-2024-Amendment-to-Civil-Aviation-Regulations-Parts-1-and-11-RE-Aerial-Works-and-Remotely-Piloted-Aircraft-Systems-Certification.pdf
            # For example, this link sometimes doesn't serve an application/pdf on the first try, but instead text/html w/ cookies, and the request must be retried with cookies so we get the application/pdf.
            # But other times, it does serve the application/pdf on the first try even without cookies in the request. Furthermore, it sometimes cares about the User-Agent header. Other times, it doesn't.
            # In this case, do not code to handle it as it may just waste our time. ¯\_(ツ)_/¯
            async with ctx.session.get(url) as resp:
                print(resp.headers.get("Content-Type"))
                if resp.headers.get("Content-Type") not in (
                    "application/pdf",
                    "application/octet-stream",  # example: https://docs.congress.hrep.online/legisdocs/basic_19/HB09867.pdf
                ):
                    return await ctx.send("ERROR: Given file / link or URL is not a PDF file")

                pdf_bytes = await resp.read()
                images = await convert_pdf_to_images(pdf_bytes)

                image_list = []
                for image in images:
                    image_bytes = BytesIO()
                    image.save(image_bytes, "JPEG")
                    image_bytes.seek(0)
                    image_list.append(discord.File(image_bytes, f"{uuid.uuid4()}.jpg"))

                if flags.selection:
                    # Note: Currently, the bot will download the entire PDF file and convert it to images before parsing the selected pages.
                    # If there's an error in the selection range, the bot will have wasted resources downloading and converting the entire PDF file,
                    # since the command terminates after the error is detected and the bot will not send any images.
                    # BUT, part of the check is to ensure that the selected pages are within the range of the total number of pages in the PDF file.
                    # So, we can't just check the selection range before downloading the PDF file. We could split the check into two parts but nah.
                    try:
                        selected_pages = parse_selected_pages(flags.selection, len(image_list))
                        print(selected_pages)
                    except ValueError:
                        return await ctx.reply("🛑 Error parsing selection range")
                    if not selected_pages:
                        return await ctx.reply("🛑 Invalid selection range")

                    # FIXME: We should instead be using the library's built-in page selection feature to avoid converting the entire PDF file,
                    # instead of converting the whole thing and then manually selecting pages from the resulting output (list) of images.
                    # This will save resources and time, especially for large PDF files. But, this might be difficult if the library only specifies
                    # a start and end page selection argument, and not free-form page selection like we have in this cmd arguments.
                    # See: https://github.com/Belval/pdf2image
                    # Get selected pages
                    image_list = [
                        # image_list[min(max(i, 1) - 1, len(image_list) - 1)]
                        image_list[i - 1]
                        for i in selected_pages
                    ]

                chunks = [image_list[x : x + 10] for x in range(0, len(image_list), 10)]

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
    async def removebg(self, ctx, url=None, attachment: Optional[discord.Attachment] = None):
        """Remove background from an image"""
        # ? Note: This might be non-blocking. If so, then there's no incentive to make the rembg library a microservice.
        # ? It seems to block, but it works very fast anyway. For now, we'll keep it as a library.
        # While it will make this bot's Docker container significantly smaller, the microservice will have to install
        # additional dependencies for it to work as a service instead of a library, which consumes more space and RAM
        # overall in our system. In here, it is just a library that is imported and used directly.

        if url is None and not ctx.message.attachments:
            return await ctx.send("Please attach an image / provide a link or URL")

        url = ctx.message.attachments[0].url if ctx.message.attachments else url
        # ? Should we add support for multiple images at once?

        async with ctx.typing():
            async with ctx.session.get(url) as resp:
                print(resp.status)
                print(resp.headers.get("Content-Type"))
                # I think PIL in rembg code should handle errors related to non-image urls

                output = remove(await resp.read())
                await ctx.send(file=discord.File(BytesIO(output), f"{uuid.uuid4()}.png"))

    @commands.hybrid_command()
    @app_commands.describe(location="Check the weather at the specified location")
    async def weather(self, ctx, location: str = "Pasig"):
        """Check the weather!"""

        async with ctx.typing():
            timeout = aiohttp.ClientTimeout(total=5)
            async with ctx.session.get(f"https://wttr.in/{location}?0T", timeout=timeout) as resp:
                resp.raise_for_status()
                text = await resp.text()
                print(f"{resp.status}, {len(text)=}, {text=}")
                if text == "" or text == "\n" or text == "Follow @igor_chubin for wttr.in updates":
                    return await ctx.send("The weather service is having problems. Please try again later.")
                # print(text)
                await ctx.send(f"```{text}```")

    # TODO: input validation, explore JSON data
    @commands.command()
    async def metar(self, ctx, airport_code: str = "RPLL"):
        async with ctx.typing():
            query_url = f"https://avwx.rest/api/metar/{airport_code}"
            async with ctx.session.get(
                query_url, headers={"Authorization": "BEARER " + os.getenv("METAR_TOKEN")}
            ) as response:
                print(response.status)
                response.raise_for_status()
                json_data = await response.json()
                print(json_data)
                if response.status == 204:
                    return await ctx.send(f"Unexpected HTTP `204 No Content` response from {query_url}")
                await ctx.send(json_data["raw"])

    @app_commands.command()
    @app_commands.describe(url="The direct link to the file")
    async def repost(self, interaction: discord.Interaction, url: str, filename: str = None):
        """Reposts the file located at the given URL (subject to 25MB non-boosted server limitation)"""

        await interaction.response.defer()

        async with self.bot.session.get(url) as resp:  # TODO: Currently does not validate URLs
            print(f"Reposter HTTP status: {resp.status}, Content length: {resp.content_length}")
            if resp.status == 200:
                file_bytes = BytesIO(await resp.read())
                filename = filename or os.path.basename(urlparse(url).path)
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
                    await interaction.followup.send(content=f"HTTPException: {e}", ephemeral=True)
            else:
                await interaction.followup.send(content="Did not return 200 status code", ephemeral=True)

    @commands.hybrid_command(aliases=["tag-show", "tagshow"])
    @app_commands.describe(name="The name of the tag to find")
    async def tag(self, ctx: Context, name: str):
        """Finds a tag with the given name and displays its content"""

        name = name.lower()

        # Find the tag by name
        tag = await self.tags_manager.find_tag_by_name(name)

        # If the tag is not found, send an error message
        if not tag:
            await ctx.send("That tag does not exist.")
            return

        # Send the tag content
        # ? Add owner as embed text footer
        await ctx.send(tag.content)

    @commands.hybrid_command(name="tag-create", aliases=["tagcreate", "tag-add", "tagadd"])
    @app_commands.describe(name="The name of the tag to be created")
    @app_commands.describe(content="The content of the tag to be created")
    async def tag_create(
        self,
        ctx: Context,
        name: commands.Range[str, None, 211],
        *,
        content: commands.Range[str, None, MessageLimit.CONTENT.value],
    ):
        """Creates a tag with the given name and content"""

        name = name.lower()

        # Check if the tag already exists
        if await self.tags_manager.find_tag_by_name(name):
            await ctx.send("🛑 That tag already exists.")
            return

        author = ctx.author
        await self.tags_manager.insert_tag(name, content, author.id)

        await ctx.send(f'✅ Tag "{name}" successfully created.')

    @commands.hybrid_command(name="tag-list", aliases=["taglist"])
    @app_commands.describe(user="The user to list tags for")
    async def tag_list(self, ctx: Context, user: discord.User = None):
        """Lists tags by user"""

        # If no user is specified, use the author of the command
        if user is None:
            user = ctx.author

        # Get the tags for the user
        tags = await self.tags_manager.find_tags_by_user_id(user.id)

        # If the user has no tags, send an error message
        if not tags:
            await ctx.send("⚠️ No tags found.")
            return

        # Format the tags as a string
        tag_list = "\n".join(f"- {tag.name}" for tag in tags)

        # Send the list of tags
        await ctx.send(f"Tags for {user.display_name}:\n{tag_list}")

    # TODO: Implement tag-seach

    @commands.hybrid_command(name="tag-delete", aliases=["tagdelete", "tag-rm", "tagrm"])
    @app_commands.describe(name="The name of the tag to delete")
    async def tag_delete(self, ctx: Context, name: str):
        """Deletes a tag with the given name"""

        name = name.lower()

        # Find the tag by name
        tag = await self.tags_manager.find_tag_by_name(name)

        # If the tag is not found, send an error message
        if not tag:
            await ctx.send("⚠️ That tag does not exist.")
            return

        # Check if the author of the command is the owner of the tag
        # FIXME: Allow bot owner to delete any tag
        # FIXME: If you look at the quote equivalent, the style of checks is different. Make the two consisent across all functions.
        if ctx.author.id != int(tag.owner):
            await ctx.send("🛑 You do not own that tag.")
            return

        # Delete the tag
        await self.tags_manager.delete_tag_by_name(name)
        # Send a confirmation message
        # ? Maybe add ownership info
        await ctx.send(f'✅ Tag "{name}" successfully deleted.')


async def setup(bot):
    engine = bot.db_engine
    tags_manager = TagsManager(engine)

    await bot.add_cog(Tools(bot, tags_manager))
