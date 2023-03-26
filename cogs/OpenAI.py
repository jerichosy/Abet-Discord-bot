import asyncio
from typing import Literal

import discord
import openai
from discord.ext import commands
from dotenv import load_dotenv
from openai.error import RateLimitError

import cogs.utils.character_limits as character_limits
from cogs.utils.ExchangeRateUSDPHP import ExchangeRateUSDPHP

load_dotenv()


class ConfirmPrompt(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

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
        await interaction.message.delete()
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
        self.value = False
        self.stop()


class OpenAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["ask", "ask-gpt", "chat"])
    @commands.cooldown(rate=1, per=8, type=commands.BucketType.member)
    @commands.max_concurrency(number=1, per=commands.BucketType.member, wait=False)
    async def chatgpt(
        self, ctx, *, prompt: str, model: Literal["gpt-4", "gpt-3.5-turbo"] = "gpt-4"
    ):
        """Ask ChatGPT! Now powered by OpenAI's newest GPT-4 model."""

        # FIXME: This logic is borked when this cmd is invoked thru slash
        if not ctx.interaction:
            trigger_words_translate = ["translate", "translation"]
            trigger_words_translate_match = any(
                [word in prompt.lower() for word in trigger_words_translate]
            )
            if trigger_words_translate_match:
                view = ConfirmPrompt()
                view.message = await ctx.send(
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
                    # if retry_attempt < 5:
                    #     raise RateLimitError
                    # else:
                    response = await openai.ChatCompletion.acreate(**kwargs)

                    if sent:
                        await sent.delete()

                    return response
                except RateLimitError as e:
                    if retry_attempt == max_retries:
                        raise e  # Re-raise the error if we've reached the max number of retries

                    delay = min(max_delay, min_delay * (2 ** (retry_attempt - 1)))
                    inform_delay = f"{ctx.author.mention} Your request errored. Retrying in {delay:.1f} seconds..."
                    if sent:
                        await sent.edit(content=inform_delay)
                    else:
                        sent = await ctx.channel.send(inform_delay)
                    await asyncio.sleep(delay)

        print(f"Prompt: {prompt}\nModel: {model}")
        async with ctx.typing():  # Manipulated into ctx.interaction.response.defer() if ctx.interaction
            response = await completion_with_backoff(
                model=model, messages=[{"role": "user", "content": prompt}]
            )

            answer = response["choices"][0]["message"]["content"]
            print("Length:", len(answer))

            # Calculate token cost  (Note: Using floats here instead of decimal.Decimal acceptible enough for this use case)
            # gpt-3.5-turbo	    $0.002 / 1K tokens
            print(response["usage"])
            token_prompt = response["usage"]["prompt_tokens"]
            token_completion = response["usage"]["completion_tokens"]
            if model == "gpt-3.5-turbo":
                pricing_prompt = 0.002
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
                if len(prompt) > character_limits.EMBED_TITLE_LIMIT:
                    title_ellipsis = " ..."
                    embed.title = (
                        prompt[
                            : character_limits.EMBED_TITLE_LIMIT - len(title_ellipsis)
                        ]
                        + title_ellipsis
                    )
                else:
                    embed.title = prompt

            # If answer is long, truncate it and inform in embed
            if len(answer) > character_limits.EMBED_DESC_LIMIT:
                answer_ellipsis = f" ... (truncated due to {character_limits.EMBED_DESC_LIMIT} character limit)"
                embed.description = (
                    answer[: character_limits.EMBED_DESC_LIMIT - len(answer_ellipsis)]
                    + answer_ellipsis
                )
                # embed.title = f"Truncated due to {character_limits.EMBED_DESC_LIMIT} character limit"
            else:
                embed.description = answer

            # print("Truncated length: ", len(answer))

            await ctx.reply(embed=embed, mention_author=False)

            # print(response)


async def setup(bot):
    # Get USD to PHP exchange rate for use in calculating token cost
    global currency_USD_PHP
    currency_USD_PHP = ExchangeRateUSDPHP()

    await bot.add_cog(OpenAI(bot))
