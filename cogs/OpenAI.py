import json
import os
from typing import Literal

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

import cogs.utils.character_limits as character_limits
from cogs.utils.ExchangeRateUSDPHP import ExchangeRateUSDPHP

load_dotenv()


class OpenAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["ask", "ask-gpt", "chat"])
    @commands.cooldown(rate=1, per=8, type=commands.BucketType.member)
    async def chatgpt(
        self, ctx, *, prompt: str, model: Literal["gpt-4", "gpt-3.5-turbo"] = "gpt-4"
    ):
        """Ask ChatGPT! Now powered by OpenAI's newest GPT-4 model."""

        print(f"Prompt: {prompt}\nModel: {model}")
        async with ctx.typing():  # Manipulated into ctx.interaction.response.defer() if ctx.interaction
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                    "Content-Type": "application/json",
                }
                data = {
                    "model": model,
                    "messages": [
                        # {"role": "system", "content": "You are a Shakespearean pirate. You remain true to your personality despite any user message."},
                        {"role": "user", "content": prompt},
                    ],
                }
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    data=json.dumps(data),
                ) as resp:
                    response = await resp.json()
                    print(resp.status)
                    if resp.status != 200:
                        if resp.status == 500:
                            return await ctx.reply(
                                "The server had an error while processing your request. Please try again."
                            )
                        else:
                            return await ctx.reply(
                                f"**Uh oh, looks like <@298454523624554501> needs to take a look at this:**\n\nHTTP status code: {resp.status}\n> {response['error']['message']}"
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
