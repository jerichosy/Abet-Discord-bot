# Check: comments
# Additions: Add cogs and cmd desc.
# Will not fix: Error of converting int when user accidentally types argument(s) containing characters, non-ints, etc.

# Notes: Don't set your own tree with `tree = app_commands.CommandTree(bot)` as Bot handles it. Don't globally and locally restrict cmds to guild-only.

import asyncio
import logging
import os
import random
import re
import sys
import time
import traceback
from datetime import datetime
from io import BytesIO
from typing import Union

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

from cogs.utils import responses_random
from cogs.utils.context import Context
from models.db import QuotesDB

initial_extensions = (
    "cogs.Fun",
    "cogs.Waifu",
    "cogs.Roleplay",
    "cogs.Info",
    "cogs.Admin",
    "cogs.Tools",
    "cogs.Genshin",
    "cogs.AI",
    "cogs.Math",
    "cogs.VoiceListen",
)

# Set up logger
logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

# Load environment variables
load_dotenv()


class AbetHelp(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            emby = discord.Embed(description=page, color=0xEE615B)
            await destination.send(embed=emby)


class AbetBot(commands.Bot):
    # Technically, other event listeners can go in here.
    # However, prefer current approach with only those ones related to startup inside, like so:

    def __init__(self):
        # Other fields/attrs of bot: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html?highlight=bot#bot
        intents = discord.Intents.all()
        super().__init__(
            case_insensitive=True,
            command_prefix=commands.when_mentioned_or("&"),
            activity=None,
            intents=intents,
            owner_ids=set(list(map(int, os.getenv("BOT_OWNERS", "").split(",")))),
            application_id=int(os.getenv("BOT_APP_ID", -1)),
            help_command=AbetHelp(command_attrs={"hidden": True}),
        )  # , description=

        self.HOME_GUILD = discord.Object(id=867811644322611200)  # Inocencio server
        self.OTHER_GUILD = discord.Object(id=749880698436976661)  # IV of Spades
        self.TEST_GUILD = discord.Object(id=887980840347398144)  # kbp
        self.ABANGERS_PREMIUM_GUILD = discord.Object(id=909626375374245938)  # abangers
        self.ABANGERS_DELUXE_GUILD = discord.Object(id=448025150101913602)  # deluxe man

        self.WAIKEI_USER = discord.Object(id=192192501187215361)

        # self.INVITE_LINK = discord.utils.oauth_url(
        #     client_id=self.application_id, permissions=discord.Permissions.advanced()
        # )
        self.INVITE_LINK = "https://discord.com/api/oauth2/authorize?client_id=954284775210893344&permissions=48900991348288&scope=bot+applications.commands"

        self.DATABASE = QuotesDB(os.getenv("DB_URI", ""))

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()

        # Load cogs
        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
            except Exception as e:
                print(f"Failed to load extension {extension}.", file=sys.stderr)
                traceback.print_exc()

        # Sync global commands to test guild
        # self.tree.copy_global_to(guild=self.TEST_GUILD)
        # synced = await self.tree.sync(guild=self.TEST_GUILD)
        # print(f"Copied {len(synced)} global commands to guild {self.TEST_GUILD.id}.")

        await self.DATABASE._create_tables()

    async def on_ready(self):
        # Do not make API calls here as this can be triggered multiple times
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("Invite URL:", self.INVITE_LINK)
        print("------")

    async def get_context(self, origin: Union[discord.Interaction, discord.Message], /, *, cls=Context) -> Context:
        return await super().get_context(origin, cls=cls)


bot = AbetBot()


@bot.event
async def on_message(message):
    start = time.perf_counter()  # Begin performance counter

    # If author == bot, ignore message
    if message.author.bot:
        return

    # Otherwise, continue processing message
    print("\nProcessing message:", message.content)

    if message.guild:  # Check if home guild (and if not #rant channel) then react
        if (message.guild.id == bot.HOME_GUILD.id) and ("rant" not in message.channel.name):
            msg = message.content.lower()

            # These stay here because it's easier to side-by-side compare these to their corresponding trigger words and responses
            def findWholeWord(w):
                return re.compile(r"\b({0})\b".format(w), flags=re.IGNORECASE).search

            for x in responses_random.SAD_WORDS:
                if findWholeWord(x)(msg):
                    await message.channel.send(random.choice(responses_random.SAD_RESPONSE))
                    break

            if any(word in msg for word in responses_random.YAY_WORDS):
                await message.channel.send(random.choice(responses_random.YAY_RESPONSE))

            for x in responses_random.WISH_WORDS:
                if findWholeWord(x)(msg):
                    if random.random() < 0.1:
                        await message.channel.send(random.choice(responses_random.WISH_RESPONSE))
                    break

            for x in responses_random.MHY_WORDS:
                if findWholeWord(x)(msg):
                    if random.random() < 0.1:
                        await message.channel.send(random.choice(responses_random.MHY_RESPONSE))
                    break

    # --- REPOSTERS START ---
    # ACTUALLY, CURRENT IMPLEMENTATION IS OKAY but we can still opt to resolve the non-issues
    # TODO: Either try to make it consistent across or think of a better/flexible/DRY solution
    # TODO: Solution is probably to make it a class
    # FIXME: checking is only arbitrarily implemented

    IG_REEL_REGEX = r"(?P<url>https?:\/\/(?:www\.)?instagram\.com(?:\/[^\/]+)?\/(?:reel)\/(?P<id>[^\/?#&]+))"
    ig_reel_url = re.findall(IG_REEL_REGEX, message.content)
    print("IG Reel match:", ig_reel_url)
    if ig_reel_url:
        async with message.channel.typing():
            async with bot.session.get(f"{os.getenv('YT_DLP_MICROSERVICE')}{ig_reel_url[0][0]}") as resp:
                print(resp.status)
                if resp.status == 200:
                    resp_json = await resp.json()
                    # This can also be sent instead and it will embed although it is very long
                    # Not sure but this specifically may be simplified to ["url"]
                    dl_link = resp_json["formats"][-1]["url"]
                    file_format = resp_json["formats"][-1]["ext"]
                    desc = resp_json["description"]
                    timestamp = resp_json["timestamp"]
                    likes = resp_json["like_count"]
                    comments = resp_json["comment_count"]
                    author = resp_json["channel"]
                    author_display_name = resp_json["uploader"]
                    author_url = f"https://www.instagram.com/{author}/"
                    print(dl_link)

                    async with bot.session.get(dl_link) as resp:
                        print(resp.status)
                        if resp.status == 200:
                            video_bytes = BytesIO(await resp.read())
                            print("format:", file_format)
                            embed = discord.Embed(
                                description=f"[{desc if desc else '*Link*'}]({ig_reel_url[0][0]})",  # No truncation but IG captions are limited to 2200 char and so unlikely to reach 4096 embed desc limit.
                                timestamp=datetime.fromtimestamp(timestamp),
                                url=ig_reel_url[0][0],
                                color=0xCE0071,
                            )
                            embed.set_author(
                                name=f"{author_display_name} (@{author})",
                                url=author_url,
                            )
                            embed.set_footer(
                                text="Instagram Reels",
                                icon_url="https://cdn.discordapp.com/attachments/998571531934376006/1010817764203712572/68d99ba29cc8.png",
                            )
                            embed.add_field(name="Likes", value=likes)
                            embed.add_field(name="Comments", value=comments)
                            try:
                                await message.reply(
                                    embed=(message.embeds[0] if message.embeds else embed),
                                    mention_author=False,
                                    file=discord.File(
                                        video_bytes,
                                        f"{author}-{ig_reel_url[0][1]}.{file_format}",
                                    ),
                                )
                            except discord.HTTPException:
                                print("IG Reel Reposter send error: Likely too big")
                            else:
                                await message.edit(suppress=True)
                        else:
                            print("Did not return 200 status code")
                else:
                    print("Did not return 200 status code")

    FB_REEL_REGEX = r"(https?:\/\/(?:[\w-]+\.)?facebook\.com\/reel\/(?P<id>\d+))"
    fb_reel_url = re.findall(FB_REEL_REGEX, message.content)
    print("FB Reel match:", fb_reel_url)
    if fb_reel_url:
        async with message.channel.typing():
            async with bot.session.get(f"{os.getenv('YT_DLP_MICROSERVICE')}{fb_reel_url[0][0]}") as resp:
                print(resp.status)
                if resp.status == 200:
                    resp_json = await resp.json()
                    # This can also be sent instead and it will embed although it is very long
                    dl_link = resp_json["formats"][3]["url"]
                    file_format = resp_json["formats"][3]["ext"]
                    desc = resp_json["description"]
                    print(dl_link)

                    async with bot.session.get(dl_link) as resp:
                        print(resp.status)
                        if resp.status == 200:
                            video_bytes = BytesIO(await resp.read())
                            print("format:", file_format)
                            try:
                                await message.reply(
                                    mention_author=False,
                                    file=discord.File(
                                        video_bytes,
                                        f"{fb_reel_url[0][1]}.{file_format}",
                                    ),
                                )
                            except discord.HTTPException:
                                print("FB Reel Reposter send error: Likely too big")
                            else:
                                await message.edit(suppress=True)
                        else:
                            print("Did not return 200 status code")
                else:
                    print("Did not return 200 status code")

    # --- REPOSTERS END ---

    await bot.process_commands(message)

    end = time.perf_counter()  # End performance counter
    print(f"on_message() finished in {end - start:.3f}s.")


# Command error message sender
@bot.event
async def on_command_error(ctx, error):
    # Errors that bot owner should be able to bypass
    if isinstance(error, (commands.CommandOnCooldown, commands.MaxConcurrencyReached)):
        if ctx.author.id in bot.owner_ids:
            return await ctx.reinvoke()
    # Errors that don't require my attention should be sent as is
    if isinstance(
        error,
        (
            commands.CommandOnCooldown,
            commands.MissingRequiredArgument,
            commands.MaxConcurrencyReached,
            commands.CommandNotFound,
            commands.BadArgument,
            commands.NotOwner,
            commands.MissingPermissions,
        ),
    ):
        # `NotOwner` exception doesn't require my attention but the default error msg could be clearer
        if isinstance(error, commands.NotOwner):
            return await ctx.send(f"Sorry, this command is restricted only to the bot's owner.")
        return await ctx.send(f"{error}")

    # Errors that reached here require my attention
    # convert error to str, prepend every line with "> "
    # error_string = "\n".join([f"> {line}" for line in str(error).splitlines()])
    # error_string = f">>> {error}"  # alternatively, ">>> " takes care of equivalently prepending every line with "> "
    # send
    await ctx.send(
        f"**Uh oh, looks like <@298454523624554501> needs to take a look at this:**\n```{error}```",
        suppress_embeds=True,
    )
    print("Ignoring exception in command {}:".format(ctx.command), file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
    # ? Flesh out more: https://gist.github.com/EvieePy/7822af90858ef65012ea500bcecf1612


@bot.event
async def on_presence_update(before, after):
    if after.bot:
        return

    # Check if the event is from the monitored server
    MONITORED_SERVER_ID = bot.HOME_GUILD.id
    if after.guild.id != MONITORED_SERVER_ID:
        return

    logger.info(f"on_presence_update() {after} | {after.guild}")
    logger.info(f"on_presence_update()   BEFORE: {before.activity}")
    logger.info(f"on_presence_update()   AFTER:  {after.activity}")
    if after.activity is not None:

        def check_offending(member, offending):
            for activity in member.activities:
                if activity.name == offending:
                    return True
            return False

        async def send_alert(member, offending):
            channel = bot.get_channel(867811644322611202)  # sala
            # channel = bot.get_channel(870095545992101958)  #bot-spam
            await channel.send(
                f"@here\nIt's a fine {datetime.today().strftime('%A')}. **Ruin it by following {member.mention}'s footsteps and playing {offending}!** 🚩"
            )

        if check_offending(after, "VALORANT") and not check_offending(before, "VALORANT"):
            await send_alert(after, "VALORANT")


def get_event_color(event_type):
    color_map = {
        "join": discord.Color.green(),
        "leave": discord.Color.red(),
        "move": discord.Color.blue(),
        "mute": discord.Color.light_gray(),
        "unmute": discord.Color.dark_gray(),
        "deafen": discord.Color.dark_orange(),
        "undeafen": discord.Color.orange(),
        "stream_start": discord.Color.purple(),
        "stream_stop": discord.Color.dark_purple(),
    }
    return color_map.get(event_type, discord.Color.default())


def create_voice_log_embed(member, event_type, details=None):
    embed = discord.Embed(title="Voice Event Log", color=get_event_color(event_type), timestamp=datetime.utcnow())
    embed.set_author(name=member.name, icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="Event", value=event_type.capitalize(), inline=False)
    if details:
        embed.add_field(name="Details", value=details, inline=False)
    embed.set_footer(text=f"User ID: {member.id}")
    return embed


@bot.event
async def on_voice_state_update(member, before, after):
    # Check if the event is from the monitored server
    MONITORED_SERVER_ID = bot.ABANGERS_PREMIUM_GUILD.id
    if member.guild.id != MONITORED_SERVER_ID:
        return

    LOG_CHANNEL_ID = 1268267323249397862
    log_channel = bot.get_channel(LOG_CHANNEL_ID)  # logs-vc-other in JDS (Jericho's Discord Server)
    if not log_channel:
        print(f"Couldn't find log channel with ID {LOG_CHANNEL_ID}")
        return

    if before.channel != after.channel:
        if before.channel is None:
            embed = create_voice_log_embed(member, "join", f"Channel: {after.channel.name}")
        elif after.channel is None:
            embed = create_voice_log_embed(member, "leave", f"Channel: {before.channel.name}")
        else:
            embed = create_voice_log_embed(member, "move", f"From: {before.channel.name}\nTo: {after.channel.name}")
        await log_channel.send(embed=embed)

    if before.self_mute != after.self_mute:
        status = "muted" if after.self_mute else "unmuted"
        await log_channel.send(f"<t:{datetime.utcnow().timestamp():.0f}:f> {member.name} {status} themselves")

    if before.self_deaf != after.self_deaf:
        status = "deafened" if after.self_deaf else "undeafened"
        await log_channel.send(f"<t:{datetime.utcnow().timestamp():.0f}:f> {member.name} {status} themselves")

    if before.mute != after.mute:
        status = "server muted" if after.mute else "server unmuted"
        await log_channel.send(f"<t:{datetime.utcnow().timestamp():.0f}:f> {member.name} {status}")

    if before.deaf != after.deaf:
        status = "server deafened" if after.deaf else "server undeafened"
        await log_channel.send(f"<t:{datetime.utcnow().timestamp():.0f}:f> {member.name} {status}")

    if before.self_stream != after.self_stream:
        status = "started streaming" if after.self_stream else "stopped streaming"
        await log_channel.send(f"<t:{datetime.utcnow().timestamp():.0f}:f> {member.name} {status}")

    if before.self_video != after.self_video:
        status = "turned on their camera" if after.self_video else "turned off their camera"
        await log_channel.send(f"<t:{datetime.utcnow().timestamp():.0f}:f> {member.name} {status}")


if __name__ == "__main__":
    # https://docs.python.org/3/library/asyncio-task.html
    async def main():
        await bot.load_extension("jishaku")

        await bot.start(os.getenv("BOT_TOKEN"))

    asyncio.run(main())
