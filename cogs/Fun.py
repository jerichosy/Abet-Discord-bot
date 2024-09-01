import asyncio
import mimetypes
import os
import random
import string
import time
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
        self.riddles = [
            (
                "What comes but never arrives?",
                "tomorrow",
            ),
            (
                "I have keys but no locks. I have space but no room. You can enter, but you can't go outside. What am I?",
                "keyboard",
            ),
            (
                "What has words but never speaks?",
                "book",
            ),
            (
                "I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?",
                "echo",
            ),
        ]

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
    @commands.hybrid_command(aliases=["game"])
    async def guess(self, ctx):
        """Play a game to guess the randon number"""
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

    async def common_check(self, channel_id):
        def predicate(m):
            return m.channel.id == channel_id and m.author.id == self.bot.WAIKEI_USER.id
            # return m.channel.id == channel_id and m.author.id == 298454523624554501  # for testing w/ kyoya1101
            # return m.channel.id == channel_id and m.author.id == 249355534204010506  # for testing w/ notabamf
            # return m.channel.id == channel_id and m.author.id == 199017953922908160  # for testing w/ hemeduhh
            # return m.channel.id == channel_id and m.author.id == 982369011494957118  # for testing w/ 7emadu

        return predicate

    async def cancel_check(self, interaction):
        await interaction.response.send_message(
            f"Hey <@{self.bot.WAIKEI_USER.id}>, if you do not respond with 'cancel' in 5 seconds, the command will proceed."
        )
        check_message = await self.common_check(interaction.channel_id)
        return await self.bot.wait_for(
            "message", timeout=5.0, check=lambda m: check_message(m) and m.content.lower() == "cancel"
        )

    async def reaction_check(self, interaction):
        def check_reaction(reaction, user):
            return (
                reaction.message.channel.id == interaction.channel_id
                and user.id == self.bot.WAIKEI_USER.id
                # and user.id == 298454523624554501  # for testing w/ kyoya1101
                # and user.id == 249355534204010506  # for testing w/ notabamf
                # and user.id == 199017953922908160  # for testing w/ hemeduhh
                # and user.id == 982369011494957118  # for testing w/ 7emadu
                and str(reaction.emoji) == "👍"
            )

        await interaction.channel.send(
            "Are you sure you want to cancel? React to this message with a 👍 emoji within 5 seconds to confirm."
        )
        return await self.bot.wait_for("reaction_add", timeout=5.0, check=check_reaction)

    async def password_check(self, interaction):
        await interaction.channel.send(
            "Ok. But first, create a password that includes an uppercase letter, lowercase letter, number, special character, and is at least 10 characters long with no spaces within 15 seconds."
        )
        check_message = await self.common_check(interaction.channel_id)
        # timeout 15.0 (current) or 29.0 as testing showed that the upper-bound (w/ multiple attempts) can be 25 secs and we want them to experience the rest of the challenge without giving up in the early-middle
        # but 15.0 so that they have to at least go through it thrice (third time's a charm)
        return await self.bot.wait_for(
            "message", timeout=15.0, check=lambda m: check_message(m) and self.check_password_criteria(m.content)[-1]
        )

    async def palindrome_password_check(self, interaction):
        await interaction.channel.send(
            "Now, make your password a palindrome while still meeting the criteria, within 15 seconds."
        )
        check_message = await self.common_check(interaction.channel_id)
        return await self.bot.wait_for(
            "message",
            timeout=15.0,  # FIXME: adjust timeout
            check=lambda m: check_message(m)
            and self.is_palindrome(m.content)
            and self.check_password_criteria(m.content)[-1],
        )

    async def water_emoji_memegen(self, palindrome_msg_content):
        body = """
            {
            "background": "https://64.media.tumblr.com/3d86c59d3adfa6cf085c35e0cf2659b9/tumblr_inline_p20k7xuTgK1qckp08_540.jpg",
            "style": "string",
            "text": [
                "yourpasswordhere"
            ],
            "layout": "string",
            "font": "string",
            "extension": "string",
            "redirect": true
        }
        """
        body = body.replace("yourpasswordhere", palindrome_msg_content)

        async with self.bot.session.request(
            method="POST",
            url="https://api.memegen.link/templates/custom",
            headers={"accept": "application/json", "Content-Type": "application/json"},
            data=body,
        ) as response:
            # TODO: In here, we can instead grab the `response.url` and have that link as part of the image which Discord will auto-embed. Check if this will be faster (and if we want the speed UX-wise.)
            response.raise_for_status()
            return BytesIO(await response.read()), mimetypes.guess_extension(response.headers.get("Content-Type"))

    async def water_emoji_check(self, interaction, palindrome_msg_content):
        try:
            file, ext = await self.water_emoji_memegen(palindrome_msg_content)
            dfile = discord.File(file, f"password_on_fire{ext}")
        except Exception as e:
            dfile = None
            print(e)
        await interaction.channel.send(
            f"Great... Now, your password is on fire 🔥! Type as many 💧 emojis as the length of your password to put it out within 25 seconds.",
            file=dfile,
        )
        check_message = await self.common_check(interaction.channel_id)
        return await self.bot.wait_for(
            "message",
            timeout=25.0,
            check=lambda m: check_message(m) and m.content.count("💧") == len(palindrome_msg_content),
        )

    async def math_question_check(self, interaction):
        question, answer = self.generate_math_question()
        await interaction.channel.send(
            f"Lastly, solve this simple math question in 10 seconds: ||{question}|| (unhide it first)"
        )
        check_message = await self.common_check(interaction.channel_id)
        return await self.bot.wait_for(
            "message", timeout=10.0, check=lambda m: check_message(m) and m.content == str(answer)
        )

    async def riddle_check(self, interaction):
        riddle, riddle_answer = random.choice(self.riddles)
        await interaction.channel.send(f"Oops, one more thing... Here's a riddle for you to answer in 10 seconds: {riddle}")
        check_message = await self.common_check(interaction.channel_id)
        return await self.bot.wait_for(
            "message", timeout=10.0, check=lambda m: check_message(m) and m.content.lower() == riddle_answer
        )

    def check_password_criteria(self, text):
        has_upper = any(c.isupper() for c in text)
        has_lower = any(c.islower() for c in text)
        has_digit = any(c.isdigit() for c in text)
        has_special = any(c in string.punctuation for c in text)
        is_long_enough = len(text) >= 10
        no_spaces = " " not in text
        return (
            has_upper,
            has_lower,
            has_digit,
            has_special,
            is_long_enough,
            no_spaces,
            all([has_upper, has_lower, has_digit, has_special, is_long_enough, no_spaces]),
        )

    # FIXME: Doesn't check for capitalization
    def is_palindrome(self, text):
        cleaned_text = "".join(c for c in text if c.isalnum()).lower()
        return cleaned_text == cleaned_text[::-1]

    def generate_math_question(self):
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        num3 = random.randint(1, 10)
        operation1 = random.choice(["+", "-", "*"])
        operation2 = random.choice(["+", "-", "*"])
        question = f"{num1} {operation1} {num2} {operation2} {num3}"
        answer = eval(question)
        return question, answer

    @waikei_group.command(name="stop-generating")
    async def stop_generating(self, interaction):
        """Stop the generation of Waikei LLM"""

        try:
            timestamps = []

            timestamps.append(time.time())
            await self.cancel_check(interaction)  # Challenge 1
            timestamps.append(time.time())
            await self.reaction_check(interaction)  # Challenge 2
            timestamps.append(time.time())
            await self.password_check(interaction)  # Challenge 3
            timestamps.append(time.time())
            palindrome_msg = await self.palindrome_password_check(interaction)  # Challenge 4
            timestamps.append(time.time())
            await self.water_emoji_check(interaction, palindrome_msg.content)  # Challenge 5
            timestamps.append(time.time())
            await self.math_question_check(interaction)  # Challenge 6
            timestamps.append(time.time())
            await self.riddle_check(interaction)  # Challenge 7
            timestamps.append(time.time())

            await interaction.followup.send(
                f"Unfortunately, all challenges were completed successfully, <@{self.bot.WAIKEI_USER.id}> is now unstoppable!"
            )
        except asyncio.TimeoutError:
            await interaction.followup.send(
                f"<@{self.bot.WAIKEI_USER.id}> didn't complete the challenge in time. The command proceeds."
            )

            async with self.bot.session.post(
                f"{os.getenv('YT_DLP_MICROSERVICE')}/waikei-pretrained/stop-generating"
            ) as resp:
                # Print status line
                msg = [f"HTTP/{resp.version.major}.{resp.version.minor} {resp.status} {resp.reason}"]

                # Print headers
                for key, value in resp.headers.items():
                    msg.append(f"{key}: {value}")

                # Print content
                msg.append(f"\n{await resp.text()}")

                await interaction.channel.send("Stopping generation of Waikei LLM...\n```\n{}\n```".format("\n".join(msg)))
        finally:
            for i in range(1, len(timestamps)):
                elapsed_time = timestamps[i] - timestamps[i - 1]
                print(f"Time elapsed for challenge {i}: {elapsed_time} seconds")

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
