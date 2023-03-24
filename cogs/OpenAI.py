from typing import Literal

import discord
import openai
from discord.ext import commands
from dotenv import load_dotenv
from openai.error import RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

import cogs.utils.character_limits as character_limits
from cogs.utils.ExchangeRateUSDPHP import ExchangeRateUSDPHP

load_dotenv()


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

        # For now, do not catch the exception generated when the retry limit is hit
        @retry(
            retry=retry_if_exception_type(RateLimitError),
            wait=wait_random_exponential(min=1, max=60),
            stop=stop_after_attempt(6),
        )
        async def completion_with_backoff(**kwargs):
            try:
                return await openai.ChatCompletion.acreate(**kwargs)
                # raise RateLimitError
            except RateLimitError as e:
                await ctx.send(
                    f"{ctx.author.mention} Your request errored. Retrying...\n<@298454523624554501>"
                )
                raise e

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
