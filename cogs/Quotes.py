# Samir Copyright Services
#
# Wai Kei Li has no rights to his content, quotes, knowledge, data leaks.
# All of the aforementioned are collectively owned by Samir Corp


from typing import Optional, Sequence

import discord
from discord import app_commands
from discord.ext import commands

from models.db import QuotesManager

from .utils.character_limits import MessageLimit, truncate
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
    async def quote_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get a random quote and send an interaction response using the same view
        # FIXME: Would be better to invoke the command than to call the function directly
        quote = await self.fun_instance.get_random_quote(self.member)
        if quote:
            await interaction.response.send_message(content=f"{quote} -{self.member.display_name}", view=self)
            self.message = await interaction.original_response()
        else:
            # If no quotes found, send a notice without the buttons
            await interaction.response.send_message(content=f"No quotes found for {self.member.display_name}.")

        # Remove buttons on the current interaction (i.e., "previous" msg.)
        # through its webhook (`followup`) since we can't edit an interaction response anymore as it's already been responded
        await interaction.followup.edit_message(interaction.message.id, view=None)


class QuoteListView(discord.ui.View):
    def __init__(
        self,
        fun_instance,
        member: discord.Member,
        page: int,
        per_page: int,
        timeout: Optional[float] = 180,
    ):
        super().__init__(timeout=timeout)
        self.fun_instance = fun_instance
        self.member = member
        self.page = page
        self.per_page = per_page

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

        await self.message.edit(view=self)

    @discord.ui.button(emoji="◀️")
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(1, self.page - 1)
        quotes = await self.fun_instance.get_quotes_list(self.member, self.page, self.per_page)
        embed = await self.fun_instance.create_quotes_embed(self.member, quotes)
        await interaction.response.edit_message(content=f"> Page {self.page}", embed=embed, view=self)

    @discord.ui.button(emoji="▶️")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = self.page + 1
        quotes = await self.fun_instance.get_quotes_list(self.member, self.page, self.per_page)
        embed = await self.fun_instance.create_quotes_embed(self.member, quotes)
        await interaction.response.edit_message(content=f"> Page {self.page}", embed=embed, view=self)


# TODO: Turn some stuff here into groups
class Quotes(commands.Cog):
    def __init__(self, bot, quotes_manager: QuotesManager):
        self.bot = bot
        self.quotes_manager = quotes_manager

    async def cog_check(self, ctx):
        # Only allow commands in this cog in guilds
        in_guild = ctx.guild is not None
        # print(f"{ctx.command.name} is invoked in guild: {in_guild}")
        if not in_guild:
            raise commands.NoPrivateMessage()
        return True

    async def get_random_quote(self, member: discord.Member):
        result = await self.quotes_manager.find_random_quote(member.id)
        return result.quote if result else None

    async def get_quotes_list(self, member: discord.Member, page: int = 1, per_page: int = 20):
        return await self.quotes_manager.find_quotes_by_member_id(member.id, page, per_page)

    async def create_quotes_embed(self, member: discord.Member, quotes: Sequence) -> discord.Embed:
        if not quotes:
            return discord.Embed(description="⚠️ No quotes found.")

        embed = discord.Embed(description=f"**{member.mention} quotes:**\n")
        for quote in quotes:
            embed.add_field(
                name="",
                # Truncate whole embed's field.value as quote.id length is unbounded
                value=truncate(f"**{quote.id}**: {quote.quote}", 298),
                inline=False,
            )
        return embed

    @commands.hybrid_command()
    @app_commands.describe(member="The member you want a random quote from")
    async def quote(self, ctx: Context, member: discord.Member = None):
        """random quotes (formerly Waikei as a Service)"""

        # If we're in CS-ST Friends and Co or Bored, default to waikei and get his discord.Member object
        if ctx.guild.id in (
            self.bot.ABANGERS_PREMIUM_GUILD.id,
            self.bot.ABANGERS_DELUXE_GUILD.id,
        ):
            # But if the user specified a member, use that instead
            member = member if member else await ctx.guild.fetch_member(self.bot.WAIKEI_USER.id)

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
    async def quote_add(
        self,
        ctx: Context,
        member: discord.Member,
        *,
        quote: commands.Range[str, None, 1966],
    ):
        """Adds a new quote to the collection."""

        if await self.quotes_manager.find_if_quote_exists_by_quote(quote, member.id):
            await ctx.send("🛑 That quote already exists!")
            return

        quote_id = await self.quotes_manager.insert_quote(quote, member.id, ctx.author.id)

        await ctx.send(
            # Truncate `quote` only as member.display_name is bounded to a limit of 32 chars.
            f"✅ {member.display_name} quote (ID: {quote_id}) **added**!\n\n>>> {truncate(quote, 1943)}"
        )

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
            member = member if member else await ctx.guild.fetch_member(self.bot.WAIKEI_USER.id)

        # If the user didn't specify a member (happens outside CS-ST Friends and Co), return
        if not member:
            return await ctx.send("Please specify a member.")

        quotes = await self.get_quotes_list(member, 1, 20)

        if not quotes:
            await ctx.send(embed=discord.Embed(description="⚠️ No quotes found."))
            return

        view = QuoteListView(self, member, 1, 20)
        embed = await self.create_quotes_embed(member, quotes)

        view.message = await ctx.send(
            content="> Page 1",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(users=False),
            view=view,
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

        quote = await self.quotes_manager.find_quote_by_id(quote_id)

        if quote is None:
            await ctx.send("⚠️ Quote not found.")
            return

        member = await ctx.guild.fetch_member(quote.quote_by)

        if ctx.author.id == int(quote.added_by) or ctx.author.id in self.bot.owner_ids:
            await self.quotes_manager.delete_quote_by_id(quote_id)
            await ctx.send(
                # Truncate whole sent string as quote_id length is unbounded
                truncate(
                    f"✅ Quote ID {quote_id} by {member.display_name} has been **deleted**.\n\n>>> {quote.quote}",
                    MessageLimit.CONTENT.value,
                )
            )
        else:
            await ctx.send("🛑 You do not have permission to delete this quote.")


async def setup(bot):
    engine = bot.db_engine
    quotes_manager = QuotesManager(engine)

    await bot.add_cog(Quotes(bot, quotes_manager))