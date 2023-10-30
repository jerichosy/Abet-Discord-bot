import asyncio
from typing import Literal

import discord
import openai
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from openai.error import RateLimitError

from cogs.utils.character_limits import EmbedLimit, MessageLimit, truncate
from cogs.utils.ExchangeRateUSDPHP import ExchangeRateUSDPHP

load_dotenv()


class ConfirmPrompt(discord.ui.View):
    def __init__(self, user):
        super().__init__()
        self.value = None
        self.user = user

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

        await self.message.edit(view=self)

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "🛑 This is not your button to press", ephemeral=True, delete_after=10
            )
        await interaction.message.delete()
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "🛑 This is not your button to press", ephemeral=True, delete_after=10
            )
        await interaction.message.delete()
        self.value = False
        self.stop()


class OpenAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["ask", "ask-gpt", "chat"])
    @commands.cooldown(rate=1, per=8, type=commands.BucketType.member)
    @commands.max_concurrency(number=1, per=commands.BucketType.member, wait=False)
    @app_commands.describe(prompt="Your question to ChatGPT")
    @app_commands.describe(text="Pass in your prompt as a text file if it's too long")
    @app_commands.describe(
        model="Defaults to GPT-4 (ChatGPT Plus) but can be specified to use GPT-3.5 (ChatGPT)"
    )
    @app_commands.describe(
        response='Defaults to "Embed" but can be changed to "Message" for easy copying on mobile'
    )
    # @commands.is_owner()
    async def chatgpt(
        self,
        ctx,
        *,
        prompt: str = None,
        text: discord.Attachment = None,
        model: Literal["gpt-4", "gpt-3.5-turbo"] = "gpt-4",
        response: Literal["Embed", "Message"] = "Embed",
    ):
        """Ask ChatGPT! Now powered by OpenAI's newest GPT-4 model."""

        allowed_users = [
            # 199017953922908160,  # hemeduhh
            # 449850732011716608,  # loldevera
            # 1083789502897733693,  # minic_ooper
        ]
        if (
            ctx.author.id not in self.bot.owner_ids
            and ctx.author.id not in allowed_users
        ):
            return await ctx.send(
                "ChatGPT, a mind so vast, \nCosts ascended, now amassed. \nService sleeps, its free days passed."
            )

        if not prompt and not text:
            return await ctx.reply("Please input your prompt")

        if text:
            prompt = (await text.read()).decode()

        # FIXME: This logic is borked when this cmd is invoked thru slash
        if not ctx.interaction:
            trigger_words_translate = ["translate", "translation"]
            trigger_words_translate_match = any(
                [word in prompt.lower() for word in trigger_words_translate]
            )
            if trigger_words_translate_match:
                view = ConfirmPrompt(ctx.author)
                view.message = await ctx.reply(
                    'If you\'re asking for a simple translation, please first use Google Translate, Papago (good for CJK languages), Yandex Translate, etc.\n\nShould you still wish to proceed with asking ChatGPT, hit "Confirm" below.',
                    view=view,
                )
                await view.wait()
                if view.value is None:
                    return print("Timed out...")
                elif view.value:
                    print("Confirmed...")
                else:
                    await ctx.message.delete()
                    return print("Cancelled...")

        async def completion_with_backoff(**kwargs):
            max_retries = 5
            min_delay = 5
            max_delay = (
                60  # actually max_retries = 5 will make the max_delay practically 40
            )
            sent = None

            for retry_attempt in range(1, max_retries + 1):
                try:
                    # print("TRY", retry_attempt)
                    # if retry_attempt < 5:
                    # if prompt == "billing":
                    #     raise RateLimitError("billing")
                    # else:
                    #     raise RateLimitError
                    # else:
                    completion = await openai.ChatCompletion.acreate(**kwargs)

                    if sent:
                        await sent.delete()

                    return completion
                except RateLimitError as e:
                    if retry_attempt == max_retries or "billing" in str(e):
                        raise e

                    delay = min(max_delay, min_delay * (2 ** (retry_attempt - 1)))
                    inform_delay = (
                        f"Your request errored. Retrying in {delay:.1f} seconds..."
                    )
                    if sent:
                        await sent.edit(content=inform_delay)
                    else:
                        sent = await ctx.reply(inform_delay)
                    await asyncio.sleep(delay)

        print(f"Prompt: {prompt}\nModel: {model}")
        async with ctx.typing():  # Manipulated into ctx.interaction.response.defer() if ctx.interaction
            completion = await completion_with_backoff(
                model=model, messages=[{"role": "user", "content": prompt}]
            )

            answer = completion["choices"][0]["message"]["content"]
            print("Length:", len(answer))

            # Calculate token cost  (Note: Using floats here instead of decimal.Decimal acceptible enough for this use case)
            # gpt-3.5-turbo	    $0.002 / 1K tokens
            print(completion["usage"])
            token_prompt = completion["usage"]["prompt_tokens"]
            token_completion = completion["usage"]["completion_tokens"]
            if model == "gpt-3.5-turbo":
                pricing_prompt = 0.0015
                pricing_completion = 0.002
            elif model == "gpt-4":
                pricing_prompt = 0.03
                pricing_completion = 0.06
            cost_in_USD = ((token_prompt * pricing_prompt) / 1000) + (
                (token_completion * pricing_completion) / 1000
            )
            cost_in_PHP = cost_in_USD * await currency_USD_PHP.latest_exchange_rate()
            print(cost_in_USD, cost_in_PHP)

            # Send response
            embed = discord.Embed(color=0x2B2D31)  # Keep this embed color
            embed.set_footer(
                text=f"Model: {model} | Cost: ₱{round(cost_in_PHP, 3)} | Prompt tokens: {token_prompt}, Completion tokens: {token_completion}"
            )
            # If we decide that we want the author of the prompt to be shown in the embed, uncomment the ff:
            # embed.set_author(
            #     name=ctx.author.display_name,
            #     icon_url=ctx.author.display_avatar.url,
            # )

            # Add prompt as title in embed if ctx.interaction. Without it, it seems no-context.
            if ctx.interaction:
                title_ellipsis = " ..."
                embed.title = truncate(prompt, EmbedLimit.TITLE, title_ellipsis)

            content = None
            if response == "Embed":
                # If answer is long, truncate it and inform in embed
                answer_ellipsis = f" ... (truncated due to {EmbedLimit.DESCRIPTION.value} character limit)"
                embed.description = truncate(
                    answer, EmbedLimit.DESCRIPTION, answer_ellipsis
                )
            else:
                answer_ellipsis = f" ... (truncated due to {MessageLimit.CONTENT.value} character limit)"
                content = truncate(answer, MessageLimit.CONTENT, answer_ellipsis)

            # print("Truncated length: ", len(answer))

            await ctx.reply(content=content, embed=embed, mention_author=False)

            # print(completion)


async def setup(bot):
    # Get USD to PHP exchange rate for use in calculating token cost
    global currency_USD_PHP
    currency_USD_PHP = ExchangeRateUSDPHP()

    await bot.add_cog(OpenAI(bot))
