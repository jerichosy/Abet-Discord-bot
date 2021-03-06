# Check: ~~dependencies~~, comments
# Change: Consider pulling AniList info straight from Trace.moe instead to improve response time and simplify
# Additions: Add cogs and cmd desc.
# Will not fix: Error of converting int when user accidentally types argument(s) containing characters, non-ints, etc.

# Notes: don't set your own tree with `tree = app_commands.CommandTree(bot)` as Bot handles it

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import io
import asyncio
import aiohttp
import random
from datetime import datetime
import time
import re

import traceback
import sys

import logging

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)

load_dotenv()

initial_extensions = [
    "cogs.Fun",
    "cogs.Waifu",
    "cogs.Roleplay",
    "cogs.Info",
    "cogs.Admin",
    "cogs.Tools",
    "cogs.Genshin",
]

intents = discord.Intents.all()


class AbetHelp(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            emby = discord.Embed(description=page, color=0xEE615B)
            await destination.send(embed=emby)


class AbetBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.HOME_GUILD = discord.Object(id=867811644322611200)  # Inocencio server
        self.OTHER_GUILD = discord.Object(id=749880698436976661)  # IV of Spades
        self.TEST_GUILD = discord.Object(id=887980840347398144)  # kbp

    async def setup_hook(self) -> None:
        # Load cogs
        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
            except Exception as e:
                print(f"Failed to load extension {extension}.", file=sys.stderr)
                traceback.print_exc()

        # Sync global commands to test guild
        self.tree.copy_global_to(guild=self.TEST_GUILD)
        synced = await self.tree.sync(guild=self.TEST_GUILD)
        print(f"Copied {len(synced)} global commands to guild {self.TEST_GUILD.id}.")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print(
            "Invite URL:",
            discord.utils.oauth_url(
                client_id=self.application_id, permissions=discord.Permissions.text()
            ),
        )
        print("------")

    # Can't make local to a class (being used by class Waifu, class Roleplay)
    async def get_waifu(self, type, category):
        url_string = f"https://api.waifu.pics/{type}/{category}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url_string) as r:
                logger.info(f"Waifu.pics: {r.status}")
                if r.status == 200:
                    json_data = await r.json()
                    waifu = json_data["url"]

        return waifu

    # Can't make local to a class (being used by class Fun)
    async def get_waifu_im_embed(self, type, category):
        type = "False" if type == "sfw" else "True"
        url_string = (
            f"https://api.waifu.im/random/?selected_tags={category}&is_nsfw={type}"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(url_string) as resp:
                logger.info(f"Waifu.im: {resp.status}")
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


# Other fields/attrs of bot: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html?highlight=bot#bot
bot = AbetBot(
    case_insensitive=True,
    command_prefix=commands.when_mentioned_or("&"),
    activity=None,
    intents=intents,
    owner_id=298454523624554501,
    application_id=954284775210893344,
    help_command=AbetHelp(command_attrs={"hidden": True}),
)  # , description=

sad_words = ["sad", "depressed", "hirap"]  # Removed: "bitch"

yay_words = ["yay", "freee"]

wish_words = [
    "should i pull",
    "pulling",
    "p\*ll",
    "rolls",
    "constellation",
    "constellations",
    "primo",
    "primos",
    "primogem",
    "primogems",
    "c6",
    "c5",
    "c4",
    "c3",
    "c2",
    "c1",
    "c0",
]

mhy_words = ["mihoyo", "hoyoverse"]

sad_response = [
    "Cheer up!",
    "Hang in there!",
    "You are a great person!",
    "Stay strong.",
    "Come on! You can do it!.",
    "It's okay",
    "It's okay I believe in you",
    "Maybe we'll get them next time",
    "Keep your head high",
    "It's okay don't listen to them",
    "You are the best!",
    "We'll get you Ice cream, you like that?",
    "Is there anything I can do to make you feel better?",
]

yay_response = [
    "I'm so proud of you!",
    "Good job!",
    "Keep it up!",
    "Keep up the good work!",
    "There you go!",
    "Hell yeah!",
    "Fuck, lets gooooooooo!",
    "Omg Yay!!!!!!!",
    "Let's gooooo!",
    "I can't believe it! You are amazing!",
    "WTF? Really?",
    "What the heck? Let's goooooooooo!",
    "I knew you could do it!",
    "<:letsgo:914430483176255488>",
    "<:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488>",
    "<:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488>",
    "<:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488>",
    "<:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488>",
    "https://cdn.discordapp.com/attachments/877238195966865498/943248232807538738/988697_558224364239923_644168573_n.png",
]

wish_response = [
    "Looks like someone's pulling today!",
    "I swear a 10 pull seems great right now",
    "What's the worse that could happen? You getting Qiqi?",
    "Don't save your gems you'll get qiqi anyways",
    # "wait don't tell me you're not going to pull?",  # Unhealthy
    "I hear that standing in the corner of mondstadt gives you a higher chance to pull a 5 star",
    "the adventurer's guild is calling. They want to watch you pull.",
    "make sure you stream if you pull.",
    # "It's just a game. Pulling won't be the end of the world.",  # Unhealthy
    "New content?",
    "The Kyoya Intelligence Agency (KIA) will be monitoring your pulls.",
]

mhy_response = [
    "Did I hear Mihoyo? That bitch.",
    # "Mihoyo loves you",
    # "Awe, we're trying our best here at Mihoyo",
    # "I promise to give you more primos in future patches - Mihoyo",
    # "Did you just BS Mihoyo? UID Saved, sending to Mihoyo servers...",
    "Hey people at Mihoyo are just trying to do their jobs",
    # "Please rate our game with a 5 star in the Play Store!",
    # "Please don't leave we need you['re money]",
    "We give all the money we make at Mihoyo to Mona",
    "All funds from Mihoyo are sent straight to Zhongli's pockets",
    "We aren't ripping you off. We're just compensating Timmie which is why we couldn't get you better rewards!",
]


def findWholeWord(w):
    return re.compile(r"\b({0})\b".format(w), flags=re.IGNORECASE).search


@bot.event
async def on_message(message):
    start_time = time.time()

    if message.author.bot:
        return

    if (message.guild.id == bot.HOME_GUILD.id) and ("rant" not in message.channel.name):
        msg = message.content.lower()

        for x in sad_words:
            if findWholeWord(x)(msg):
                await message.channel.send(random.choice(sad_response))
                break

        if any(word in msg for word in yay_words):
            await message.channel.send(random.choice(yay_response))

        for x in wish_words:
            if findWholeWord(x)(msg):
                if random.random() < 0.1:
                    await message.channel.send(random.choice(wish_response))
                break

        for x in mhy_words:
            if findWholeWord(x)(msg):
                if random.random() < 0.1:
                    await message.channel.send(random.choice(mhy_response))
                break

    tiktok_regex = r"(https?://www\.tiktok\.com/(?:embed|@(?P<user_id>[\w\.-]+)/video)/(?P<id>\d+))"
    tiktok_vm_regex = r"(https?://(?:vm|vt)\.tiktok\.com/\w+)"
    tiktok_url = re.findall(tiktok_regex, message.content)
    tiktok_vm_url = re.findall(tiktok_vm_regex, message.content)
    print(tiktok_url or tiktok_vm_url)
    if tiktok_url or tiktok_vm_url:
        async with message.channel.typing():
            async with aiohttp.ClientSession() as session:
                if tiktok_vm_url:
                    async with session.get(tiktok_vm_url[0]) as resp:
                        # print(resp.status)
                        tiktok_url = re.findall(tiktok_regex, str(resp.url))
                print(tiktok_url)
                async with session.get(
                    f"https://aqueous-reef-45135.herokuapp.com/extract?url={tiktok_url[0][0]}"
                ) as resp:
                    print(resp.status)
                    resp_json = await resp.json()
                    # This can also be sent instead and it will embed although it is very long
                    dl_link = resp_json["formats"][0]["url"]
                    file_format = resp_json["formats"][0]["ext"]
                    title = resp_json["title"]
                    url = resp_json["webpage_url"]
                    timestamp = resp_json["timestamp"]
                    views = resp_json["view_count"]
                    likes = resp_json["like_count"]
                    comments = resp_json["comment_count"]
                    author = resp_json["uploader"]
                    author_url = resp_json["uploader_url"]
                    print(dl_link)
                async with session.get(dl_link) as resp:
                    print(resp.status)
                    video_bytes = io.BytesIO(await resp.read())
                    print("format:", file_format)
                    embed = discord.Embed(
                        title=title,
                        timestamp=datetime.fromtimestamp(timestamp),
                        url=url,
                        color=0xFE2C55,
                    )
                    embed.set_author(name=author, url=author_url)
                    embed.set_footer(
                        text="TikTok",
                        icon_url="https://cdn.discordapp.com/attachments/998571531934376006/998571565539139614/TikTok_logo.png",
                    )
                    embed.add_field(name="Views", value=views)
                    embed.add_field(name="Likes", value=likes)
                    embed.add_field(name="Comments", value=comments)
                    await message.reply(
                        embed=embed,
                        mention_author=False,
                        file=discord.File(
                            video_bytes,
                            f"{tiktok_url[0][1]}-{tiktok_url[0][2]}.{file_format}",
                        ),
                    )

    await bot.process_commands(message)

    end_time = time.time()
    print(f"on_message execution time: {round((end_time - start_time) * 1000)}ms")


# Command error message sender
@bot.event
async def on_command_error(ctx, error):
    # if isinstance(error, commands.errors.CommandNotFound):
    # pass
    # else:
    await ctx.send(error)
    # Flesh out more?


@bot.event
async def on_presence_update(before, after):
    if after.guild.id == bot.HOME_GUILD.id:
        if not after.bot:
            logger.info(f"{after} | {after.guild}")
            logger.info(f"  BEFORE: {before.activity}")
            logger.info(f"  AFTER:  {after.activity}")
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
                        f"@here\nIt's a fine {datetime.today().strftime('%A')}. **Ruin it by following {member.mention}'s footsteps and playing {offending}!** ??????"
                    )

                if check_offending(after, "VALORANT") and not check_offending(
                    before, "VALORANT"
                ):
                    send_alert(after, "VALORANT")


async def main():
    await bot.load_extension("jishaku")

    await bot.start(os.getenv("BOT_TOKEN"))


asyncio.run(main())
