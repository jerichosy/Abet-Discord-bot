import asyncio
import os
import uuid
from datetime import datetime
from io import BytesIO
from typing import Literal

import discord
import google.generativeai as genai
import openai
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from openai import AsyncOpenAI

from cogs.utils.character_limits import EmbedLimit, MessageLimit, truncate
from cogs.utils.checks import owner_only
from cogs.utils.ExchangeRateUSDPHP import ExchangeRateUSDPHP


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
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
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


# Commands here may invoke AI APIs/requests that cost money. Due to this, take care to either limit access to and/or the capabilities of these commands.
# Example:
# - Only allowing certain users to use the command
# - Rate limiting
# - Not allowing users to use expensive models or prompts
class AI(commands.Cog):
    def __init__(self, bot, currency_USD_PHP: ExchangeRateUSDPHP):
        self.bot = bot
        self.currency_USD_PHP = currency_USD_PHP

    @property
    def client_openai(self):
        if not hasattr(self, "_client_openai"):
            # print("Creating AsyncOpenAI")
            account_id = os.getenv("CF_ACCOUNT_ID")
            gateway_id = os.getenv("CF_AI_GATEWAY_ID")
            self._client_openai = AsyncOpenAI(
                base_url=f"https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/openai"
            )
        # print("Returning AsyncOpenAI")
        return self._client_openai

    @property
    def client_grok(self):
        if not hasattr(self, "_client_grok"):
            account_id = os.getenv("CF_ACCOUNT_ID")
            gateway_id = os.getenv("CF_AI_GATEWAY_ID")
            self._client_grok = AsyncOpenAI(
                base_url=f"https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/grok",
                api_key=os.getenv("GROK_API_KEY"),
            )
        return self._client_grok

    @commands.hybrid_command(aliases=["ask", "ask-gpt", "chat", "gpt"])
    @commands.cooldown(rate=1, per=8, type=commands.BucketType.user)
    @commands.max_concurrency(number=1, per=commands.BucketType.user, wait=False)
    @app_commands.describe(prompt="Your question to ChatGPT")
    @app_commands.describe(image="Use GPT-4 Vision model to allow images as input and answer questions about them")
    @app_commands.describe(model="Defaults to GPT-4 (ChatGPT Plus) but can be specified to use GPT-3.5 (ChatGPT)")
    @commands.is_owner()  # If we allow everyone again, in OpenAI API Platform, set up a proj in the default org with its own API key so we can track costs specific to Abet bot's OpenAI API usage
    # For some reason, this `is_owner()` check also works with the slash cmd, but only for a hybrid cmd
    async def chatgpt(
        self,
        ctx,
        *,
        prompt: str,
        image: discord.Attachment = None,
        model: Literal["gpt-4o", "gpt-4-turbo", "gpt-4o-mini"] = "gpt-4o",
    ):
        """Ask ChatGPT! Now powered by OpenAI's newest GPT-4 model."""

        # allowed_users = [
        #     199017953922908160,  # hemeduhh
        #     449850732011716608,  # loldevera
        #     1083789502897733693,  # minic_ooper
        # ]
        # if (
        #     ctx.author.id not in self.bot.owner_ids
        #     and ctx.author.id not in allowed_users
        # ):
        #     return await ctx.send(
        #         "ChatGPT, a mind so vast, \nCosts ascended, now amassed. \nService sleeps, its free days passed."
        #     )

        # FIXME: This logic is borked when this cmd is invoked thru slash
        if not ctx.interaction:
            trigger_words_translate = ["translate", "translation"]
            trigger_words_translate_match = any([word in prompt.lower() for word in trigger_words_translate])
            if trigger_words_translate_match:
                view = ConfirmPrompt(ctx.author)
                view.message = await ctx.reply(
                    'If you\'re asking for a simple translation, please first try Google Translate, Naver Papago (good for CJK languages), Yandex Translate, etc.\n\nShould you still wish to proceed with asking ChatGPT, please "Confirm" below.',
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

        async def chat_completion_with_backoff(**kwargs):
            """This creates an OpenAI Chat Completion with a manual exponential backoff strategy in case of no responses."""
            max_retries = 5
            min_delay = 5
            max_delay = 60  # actually max_retries = 5 will make the max_delay practically 40
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
                    completion = await self.client_openai.chat.completions.create(**kwargs)

                    if sent:
                        await sent.delete()

                    return completion
                except openai.RateLimitError as e:
                    if retry_attempt == max_retries or "billing" in str(e):
                        raise e

                    delay = min(max_delay, min_delay * (2 ** (retry_attempt - 1)))
                    inform_delay = f"Your request errored. Retrying in {delay:.1f} seconds..."
                    if sent:
                        await sent.edit(content=inform_delay)
                    else:
                        sent = await ctx.reply(inform_delay)
                    await asyncio.sleep(delay)

        print(f"Prompt: {prompt}\nModel: {model}")
        async with ctx.typing():  # Manipulated into ctx.interaction.response.defer() if ctx.interaction
            SYSTEM = (
                f"Today is {datetime.now().strftime('%-m/%-d/%Y')}.\n"
                "\n"
                "Users Info:\n"
                "Your users are primarily based in Metro Manila, Philippines. They are students ranging from SHS to college, some of whom have already graduated.\n"
                "\n"
                "User Instructions:\n"
                "You are a friendly, helpful AI assistant. When you are asked to answer a multiple choice question, you should always provide both first the explanation and then the answer (i.e., let's think step by step)."
            )
            # print(SYSTEM)

            if not image:
                params = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": prompt},
                    ],
                }
            else:
                params = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": SYSTEM},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": image.url,
                                },
                            ],
                        },
                    ],
                    # To get around issue of very low `max_tokens` value by default when using GPT-4V
                    # https://community.openai.com/t/gpt-4-vision-preview-finish-details/475911/7
                    # Set to 4096 as that is the current official limit
                    # https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo#:~:text=4%20Turbo%20capabilties.-,Returns%20a%20maximum%20of%204%2C096%20output%20tokens.,-This%20is%20a
                    "max_tokens": 4096,
                }

            completion = await chat_completion_with_backoff(**params)

            # print(completion)
            answer = completion.choices[0].message.content
            print("OpenAI completion length:", len(answer))

            # Calculate token cost  (Note: Using floats here instead of decimal.Decimal acceptible enough for this use case)
            # gpt-3.5-turbo	    $0.002 / 1K tokens
            print(completion.usage)
            token_prompt = completion.usage.prompt_tokens
            token_completion = completion.usage.completion_tokens
            print(completion.model)
            if model == "gpt-4o-mini":
                pricing_prompt = 0.000150
                pricing_completion = 0.000600
            elif model == "gpt-4-turbo":
                pricing_prompt = 0.01
                pricing_completion = 0.03
            elif model == "gpt-4o":
                pricing_prompt = 0.005
                pricing_completion = 0.015
            cost_in_USD = ((token_prompt * pricing_prompt) / 1000) + ((token_completion * pricing_completion) / 1000)
            try:
                cost_in_PHP = cost_in_USD * await self.currency_USD_PHP.latest_exchange_rate()
                print(cost_in_USD, cost_in_PHP)
                footer_cost_text = f"Cost: ₱{round(cost_in_PHP, 3)} | "
            except Exception as e:
                print(e)
                footer_cost_text = ""

            # Send response
            embed = discord.Embed(color=0x74AA9C)
            embed.set_footer(
                text=f"Model: {model} | {footer_cost_text}Prompt tokens: {token_prompt}, Completion tokens: {token_completion}",
                icon_url="https://cdn.oaistatic.com/_next/static/media/favicon-32x32.be48395e.png",
            )
            # If we decide that we want the author of the prompt to be shown in the embed, uncomment the ff:
            # embed.set_author(
            #     name=ctx.author.display_name,
            #     icon_url=ctx.author.display_avatar.url,
            # )
            if image:
                embed.set_image(url=image.url)

            # Add prompt as title in embed if ctx.interaction. Without it, it seems no-context.
            if ctx.interaction or ctx.message.attachments:
                title_ellipsis = " ..."
                embed.title = truncate(prompt, EmbedLimit.TITLE.value, title_ellipsis)

            # If answer is long, truncate it and inform in embed
            answer_ellipsis = f" ... (truncated due to {EmbedLimit.DESCRIPTION.value} character limit)"
            embed.description = truncate(answer, EmbedLimit.DESCRIPTION.value, answer_ellipsis)

            # print("Truncated length: ", len(answer))

            await ctx.reply(embed=embed, mention_author=False)

            # print(completion)

    @commands.hybrid_command()
    @app_commands.describe(prompt="Your question to Elon Musk?")
    async def grok(self, ctx, *, prompt: str):
        """Ask Grok! Powered by Elon Musk's xAI."""

        model = "grok-beta"

        async with ctx.typing():
            params = {
                "model": model,
                "messages": [
                    # {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            }
            completion = await self.client_grok.chat.completions.create(**params)
            answer = completion.choices[0].message.content
            print("Grok completion length:", len(answer))

            print(completion.usage)
            token_prompt = completion.usage.prompt_tokens
            token_completion = completion.usage.completion_tokens
            print(completion.model)
            if model == "grok-beta":
                pricing_prompt = 5
                pricing_completion = 15
            cost_in_USD = ((token_prompt * pricing_prompt) / 1_000_000) + (
                (token_completion * pricing_completion) / 1_000_000
            )
            try:
                cost_in_PHP = cost_in_USD * await self.currency_USD_PHP.latest_exchange_rate()
                print(cost_in_USD, cost_in_PHP)
                footer_cost_text = f"Cost: ₱{round(cost_in_PHP, 3)} | "
            except Exception as e:
                print(e)
                footer_cost_text = ""

            # Send response
            answer_ellipsis = f" ... (truncated due to {EmbedLimit.DESCRIPTION.value} character limit)"
            embed = discord.Embed(
                description=truncate(answer, EmbedLimit.DESCRIPTION.value, answer_ellipsis), color=0x0A0A0A
            )
            embed.set_footer(
                text=f"Model: {model} | {footer_cost_text}Prompt tokens: {token_prompt}, Completion tokens: {token_completion}",
                icon_url="https://i.imgur.com/eTPBvvB.png",
            )

            # Add prompt as title in embed if ctx.interaction. Without it, it seems no-context.
            if ctx.interaction:
                title_ellipsis = " ..."
                embed.title = truncate(prompt, EmbedLimit.TITLE.value, title_ellipsis)

            await ctx.reply(embed=embed, mention_author=False)

    # TODO: Add system prompt but first check its reliability at the current state (possibly w/ history)
    # This doesn't have rate limiting as it's free
    @commands.hybrid_command(aliases=["bard"])
    async def gemini(
        self,
        ctx,
        *,
        prompt: str,
        model: Literal["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"] = "gemini-1.5-pro",
    ):
        """Ask Gemini (formely Bard)! Now powered by Google's Gemini Pro model."""

        generativemodel = genai.GenerativeModel(model)
        async with ctx.typing():
            response = await generativemodel.generate_content_async(prompt)
            # print(response)
            # print(response.text)
            # print(response.__dict__)
            # print(response.prompt_feedback)
            try:
                embed = discord.Embed(description=response.text, color=0x4285F4)
                embed.set_footer(
                    text=f"Model: {model} | Cost: Free (subject to rate limits)",
                    icon_url="https://www.gstatic.com/lamda/images/favicon_v1_70c80ffdf27202fd2e84f.png",
                )

                if ctx.interaction:
                    title_ellipsis = " ..."
                    embed.title = truncate(prompt, EmbedLimit.TITLE.value, title_ellipsis)

                await ctx.reply(embed=embed, mention_author=False)
            except ValueError:
                await ctx.reply(
                    f"No response due to the following:\n```{response.prompt_feedback}```",
                    # mention_author=False,  # Current convention in AI.py is to mention if error
                )

    @app_commands.command()
    @commands.cooldown(rate=1, per=8, type=commands.BucketType.user)
    @commands.max_concurrency(number=1, per=commands.BucketType.user, wait=False)
    @app_commands.describe(audio_file="Supports MP3, MP4, MPEG, MPGA, M4A, WAV, and WEBM. Limited to 25 MB.")
    # If we allow everyone, in OpenAI API Platform, set up a proj in the default org with its own API key so we can track costs specific to Abet bot's OpenAI API usage
    @app_commands.check(owner_only)
    async def whisper(self, interaction: discord.Interaction, audio_file: discord.Attachment):
        """Uses OpenAI's Whisper model to transcribe audio (speech) to text"""

        # Check if over 25 MB
        FILESIZE_LIMITATION = 26214400  # 25 MiB to bytes
        if audio_file.size > FILESIZE_LIMITATION:
            return await interaction.response.send_message("🛑 Your attachment is over the 25 MB filesize limit.")

        # TODO: Check if accepted format
        print(audio_file.content_type)

        # Defer before transcribing as it could take a while
        await interaction.response.defer()

        audio_filename_split = os.path.splitext(os.path.basename(audio_file.filename))

        # Save the attached file to a temporary location with its original name
        # FIXME: Saving the temp audio file may not as intended if the temp folder doesn't exist
        # FIXME: Find a way to create this if it doesn't exist already
        temp_filename = f"./temp/{uuid.uuid4()}{audio_filename_split[-1]}"  # Make sure the './temp/' directory exists or choose a suitable temp directory
        await audio_file.save(temp_filename)

        try:
            # Transcribe
            with open(temp_filename, "rb") as f:  # Open the file in binary read mode
                transcript = await self.client_openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,  # Pass the file object directly
                )
            print("Transcript done")

            # Send transcript
            FILENAME = audio_filename_split[0] + "_transcript.txt"
            await interaction.followup.send(file=discord.File(BytesIO(transcript.text.encode()), FILENAME))

        finally:
            # Clean up the temporary file
            os.remove(temp_filename)


async def setup(bot):
    # Get USD to PHP exchange rate for use in calculating token cost
    currency_USD_PHP = ExchangeRateUSDPHP(bot.session)

    await bot.add_cog(AI(bot, currency_USD_PHP))
