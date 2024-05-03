# Samir Copyright Services
#
# Wai Kei Li has no rights to his content, quotes, knowledge, data leaks.
# All of the aforementioned are collectively owned by Samir Corp


import asyncio
import random
from io import BytesIO
from typing import List, Literal, Optional, Sequence

import aiohttp
import discord
from discord import app_commands
from discord.app_commands import Group
from discord.ext import commands

from .utils.context import Context


class QuoteButtonView(discord.ui.View):
    def __init__(self, fun_instance, member):
        super().__init__()
        self.fun_instance = fun_instance
        self.member = member

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

        await self.message.edit(view=self)

    @discord.ui.button(label="Get Another Quote")
    async def quote_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # Get a random quote and send an interaction response using the same view
        quote = await self.fun_instance.get_random_quote(self.member)
        if quote:
            await interaction.response.send_message(
                content=f"{quote} -{self.member.display_name}", view=self
            )
            self.message = await interaction.original_response()
        else:
            # If no quotes found, send a notice without the buttons
            await interaction.response.send_message(
                content=f"No quotes found for {self.member.display_name}."
            )

        # Remove buttons on the current interaction (i.e., "previous" msg.)
        # through its webhook (`followup`) since we can't edit an interaction response anymore as it's already been responded
        await interaction.followup.edit_message(interaction.message.id, view=None)


class QuoteListView(discord.ui.View):
    def __init__(self, fun_instance, member: discord.Member, page: int, per_page: int, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)
        self.fun_instance = fun_instance
        self.member = member
        self.page = page
        self.per_page = per_page

    async def _create_quotes_embed(self, quotes: Sequence) -> discord.Embed:
        if not quotes:
            return discord.Embed(description="⚠️ No quotes found.")

        embed = discord.Embed(description=f"**{self.member.display_name} quotes:**\n")
        for quote in quotes:
            embed.add_field(name="", value=f"`{quote.id}`\t\t\t'{quote.quote}'", inline=False)
        return embed

    @discord.ui.button(emoji="◀️")
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(1, self.page - 1)
        quotes = await self.fun_instance.get_quotes_list(self.member, self.page, self.per_page)
        embed = await self._create_quotes_embed(quotes)
        await interaction.response.edit_message(
            content=f"> Page {self.page}",
            embed=embed, 
            view=self
        )

    @discord.ui.button(emoji="▶️")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = self.page + 1
        quotes = await self.fun_instance.get_quotes_list(self.member, self.page, self.per_page)
        embed = await self._create_quotes_embed(quotes)
        await interaction.response.edit_message(
            content=f"> Page {self.page}",
            embed=embed, 
            view=self
        )


class Fun(commands.Cog):
    def __init__(self, bot, waifu_im_tags):
        self.bot = bot
        self.waifu_im_tags = waifu_im_tags

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

    async def get_random_quote(self, member: discord.Member):
        result = await self.bot.DATABASE.find_random_quote(member.id)
        return result.quote if result else None

    async def get_quotes_list(self, member: discord.Member, page: int = 1, per_page: int = 20):
        return await self.bot.DATABASE.find_quotes_by_member_id(member.id, page, per_page)

    @commands.hybrid_command(aliases=["wai", "waikeili", "waikei"])
    @app_commands.describe(member="The member you want a random quote from")
    async def quote(self, ctx: Context, member: discord.Member = None):
        """random quotes (formerly Waikei as a Service)"""

        # If we're in CS-ST Friends and Co or Bored, default to waikei and get his discord.Member object
        if ctx.guild.id in (
            self.bot.ABANGERS_PREMIUM_GUILD.id,
            self.bot.ABANGERS_DELUXE_GUILD.id,
        ):
            # But if the user specified a member, use that instead
            member = (
                member
                if member
                else await ctx.guild.fetch_member(self.bot.WAIKEI_USER.id)
            )

        # If the user didn't specify a member (happens outside CS-ST Friends and Co), return
        if not member:
            return await ctx.send("Please specify a member.")

        quote = await self.get_random_quote(member)

        if quote:
            view = QuoteButtonView(self, member=member)  # self is the Fun instance

            # image_link_pattern = re.compile(
            #     r"(https?://\S+\.(?:jpg|jpeg|png|gif))"
            # )
            # if image_link_pattern.match(quote):
            #     await ctx.send(f"{quote}")
            # else:
            #     await ctx.send(f"{quote} -Waikei Li")
            view.message = await ctx.send(f"{quote} -{member.display_name}", view=view)
        else:
            # If no quotes found, send a notice without the buttons
            await ctx.send(f"No quotes found for {member.display_name}.")

    @commands.hybrid_command(
        # aliases=["waikei_addquote", "waikei_a", "waikei_aquote", "waikei_add"],
        name="quote-add"
    )
    @app_commands.describe(quote="DO NOT INCLUDE QUOTATION MARKS")
    async def quote_add(self, ctx: Context, member: discord.Member, *, quote: str):
        """Adds a new quote to the collection."""

        if await self.bot.DATABASE.find_if_quote_exists_by_quote(quote, member.id):
            await ctx.send("🛑 That quote already exists!")
            return

        await self.bot.DATABASE.insert_quote(quote, member.id, ctx.author.id)

        await ctx.send(f"✅ {member.display_name} quote **added**!\n\n>>> {quote}")

    @commands.hybrid_command(
        aliases=["waikei_listquote", "waikei_l", "waikei_lquote", "waikei_list"],
        name="quote-list",
    )
    async def quote_list(self, ctx: Context, member: discord.Member = None):
        """Lists all quotes with their IDs."""

        # If we're in CS-ST Friends and Co or Bored, default to waikei and get his discord.Member object
        if ctx.guild.id in (
            self.bot.ABANGERS_PREMIUM_GUILD.id,
            self.bot.ABANGERS_DELUXE_GUILD.id,
        ):
            # But if the user specified a member, use that instead
            member = (
                member
                if member
                else await ctx.guild.fetch_member(self.bot.WAIKEI_USER.id)
            )

        # If the user didn't specify a member (happens outside CS-ST Friends and Co), return
        if not member:
            return await ctx.send("Please specify a member.")

        quotes = await self.get_quotes_list(member, 1, 20)

        if not quotes:
            await ctx.send(embed=discord.Embed(description="⚠️ No quotes found."))
            return

        view = QuoteListView(self, member, 1, 20)
        embed = discord.Embed(description=f"**{member.display_name} quotes:**\n")
        for quote in quotes:
            embed.add_field(name="", value=f"**{quote.id}**\t\t\t'{quote.quote}'", inline=False)

        await ctx.send(
            content="> Page 1",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(users=False),
            view=view
        )

    # TODO: Maybe add a confirmation, but tbh not needed because quotes can only be removed by the person who added them
    @commands.hybrid_command(
        # aliases=[
        #     "waikei_deletequote",
        #     "waikei_d",
        #     "waikei_dquote",
        #     "waikei_del",
        #     "waikei_delquote",
        #     "delwaikei",
        #     "waikei_delete",
        # ],
        name="quote-delete"
    )
    @app_commands.describe(quote_id="Specify the ID of the quote shown in /quote_list")
    async def quote_delete(self, ctx: Context, quote_id: int):
        """Deletes a quote by its ID."""

        quote = await self.bot.DATABASE.find_quote_by_id(quote_id)

        if quote is None:
            await ctx.send("⚠️ Quote not found.")
            return

        member = await ctx.guild.fetch_member(quote.quote_by)

        if ctx.author.id == int(quote.added_by) or ctx.author.id in self.bot.owner_ids:
            await self.bot.DATABASE.delete_quote_by_id(quote_id)
            await ctx.send(
                f"✅ Quote ID {quote_id} by {member.display_name} has been **deleted**.\n\n>>> {quote.quote}"
            )
        else:
            await ctx.send("🛑 You do not have permission to delete this quote.")

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
            async with ctx.session.get("https://api.tronalddump.io/random/meme") as r:
                data = BytesIO(await r.read())
                await ctx.send(file=discord.File(data, "tronalddump.jpeg"))

    @commands.hybrid_command(aliases=["meow"])
    async def cat(self, ctx: Context):
        """Gives you a random cat."""
        async with ctx.session.get(
            "https://api.thecatapi.com/v1/images/search"
        ) as resp:
            if resp.status != 200:
                return await ctx.send("No cat found :(")
            js = await resp.json()
            await ctx.send(
                embed=discord.Embed(title="Random Cat").set_image(url=js[0]["url"])
            )

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
                            return await ctx.send(
                                f"Video was too big to upload... See it here: {url} instead."
                            )

                        fp = BytesIO(await other.read())
                        await ctx.send(file=discord.File(fp, filename=filename))
            else:
                await ctx.send(
                    embed=discord.Embed(title="Random Dog").set_image(url=url)
                )

    @commands.hybrid_command()
    async def uselessfact(self, ctx):
        """Not sure why I added a totally useless feature"""
        async with ctx.session.get(
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

    @staticmethod
    async def get_waifu_im_embed(type, category):
        type = "false" if type == "sfw" else "true"
        url_string = (
            f"https://api.waifu.im/search/?included_tags={category}&is_nsfw={type}"
        )
        headers = {"Accept-Version": "v5"}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url_string) as resp:
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

    @sfw.autocomplete("tag")
    async def sfw_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=waifu_im_tag, value=waifu_im_tag)
            for waifu_im_tag in self.waifu_im_tags["versatile"]
            if current.lower() in waifu_im_tag.lower()
        ]

    @nsfw.autocomplete("tag")
    async def nsfw_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=waifu_im_tag, value=waifu_im_tag)
            for waifu_im_tag in self.waifu_im_tags["nsfw"]
            if current.lower() in waifu_im_tag.lower()
        ]


async def setup(bot):
    # Populate the waifu_im_tags list (for waifu slash cmd)
    headers = {"Accept-Version": "v5"}
    async with aiohttp.ClientSession(headers=headers) as cs:
        async with cs.get("https://api.waifu.im/tags") as r:
            print(f"Waifu.im tags query status code: {r.status}\n")
            if r.status == 200:
                waifu_im_tags = await r.json()

    await bot.add_cog(Fun(bot, waifu_im_tags))
