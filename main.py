# Check: ~~dependencies~~, comments
# Change: migrate from requests to non-blocking alternative (only whatanime remaining), make it not respond to bots, Fix help cmd in "No Category", Consider pulling AniList info straight from Trace.moe instead to improve response time
# Additions: Add cogs and cmd desc.
# Will not fix: Error of converting int when user accidentally types argument(s) containing characters, non-ints, etc.

# Add in commit desc/comment: 

# Notes: requests has issues on IPv6 networks, don't set your own tree with `tree = app_commands.CommandTree(bot)`

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, Context
from discord import app_commands
from dotenv import load_dotenv
import os
import asyncio
import io
import aiohttp
import requests
import json
import random
from random import choices
from datetime import datetime, timedelta
import time
import re
import pkg_resources
import psutil
import genshinstats as gs
from collections import Counter
from typing import List, Literal, Optional

import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

load_dotenv()

intents = discord.Intents.all()
intents.message_content = True  # This might not be neccessary since we already called Intents.all()

class AbetHelp(commands.MinimalHelpCommand):
  async def send_pages(self):
    destination = self.get_destination()
    for page in self.paginator.pages:
      emby = discord.Embed(description=page, color=0xee615b)
      await destination.send(embed=emby)

class AbetBot(commands.Bot):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  async def setup_hook(self) -> None:
    # Populate the waifu_im_tags list (for slash cmds)
    async with aiohttp.ClientSession() as cs:
      async with cs.get('https://api.waifu.im/endpoints') as r:
        print(f"Waifu.im endpoint: {r.status}")
        if r.status == 200:
          global waifu_im_tags
          waifu_im_tags = json.loads(await r.text())['versatile']

  async def on_ready(self):
    print(f'Logged in as {self.user} (ID: {self.user.id})')
    print('------')

# Other fields/attrs of bot: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html?highlight=bot#bot
bot = AbetBot(case_insensitive=True, command_prefix=commands.when_mentioned_or('&'), activity=discord.Game(name="Blame my owner if I keep going offline"), intents=intents, owner_id = 298454523624554501, help_command=AbetHelp(command_attrs = {"hidden": True}))  # , description=

sad_words = ["sad", "depressed", "hirap"]  # Removed: "bitch"

yay_words = ["yay", "freee"]

wish_words = ["should i pull", "pulling", "p\*ll", "rolls", "constellation", "constellations", "primo", "primos", "primogem", "primogems", "c6", "c5", "c4", "c3", "c2", "c1", "c0", "character", "characters"]

mhy_words = ["mihoyo"]

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
  "Is there anything I can do to make you feel better?"
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
  "https://cdn.discordapp.com/attachments/877238195966865498/943248232807538738/988697_558224364239923_644168573_n.png"
]

wish_response = [
  "Looks like someone's pulling today!",
  #"I swear a 10 pull seems great right now",  # Unhealthy
  "What's the worse that could happen? You getting Qiqi?",
  "Don't save your gems you'll get qiqi anyways",
  #"wait don't tell me you're not going to pull?",  # Unhealthy
  "I hear that standing in the corner of mondstadt gives you a higher chance to pull a 5 star",
  "the adventurer's guild is calling. They want to watch you pull.",
  "make sure you stream if you pull.",
  #"It's just a game. Pulling won't be the end of the world.",  # Unhealthy
  "New content?",
  "The Kyoya Intelligence Agency (KIA) will be monitoring your pulls.",
]

mhy_response = [
  "Did I hear Mihoyo? That bitch.",
  #"Mihoyo loves you",
  #"Awe, we're trying our best here at Mihoyo",
  #"I promise to give you more primos in future patches - Mihoyo",
  #"Did you just BS Mihoyo? UID Saved, sending to Mihoyo servers...",
  #"Hey people at Mihoyo are just trying to do their jobs",
  #"Please rate our game with a 5 star in the Play Store!",
  #"Please don't leave we need you['re money]",
  "We give all the money we make at Mihoyo to Mona",
  "All funds from Mihoyo are sent straight to Zhongli's pockets",
  "We aren't ripping you off. We're just compensating Timmie which is why we couldn't get you better rewards!"
]

abet_response = [
  "Absolutely!",
  "Without a doubt!",
  "Hell Yeah!",
  "Fuck no",
  "What the fuck are these questions? *Sighs* But yes you will get what you want for some reason",
  "Dude, that's sick. It's a no though.",
  "You're chances are as high as the amount of Qiqi constellations you have",
  "Maybe, Fine. Yes.",
  "Sinasabi ng aking mahiwagang kristal it's a paking YES putangina.",
  "I heard buying KofiTreb's Coffee increases your odds",
  "If you haven't taken a bath in the past 3 days it's a yes",
  "Bruh.",
  "Hell no.",
  "My magic balls says fuck yeah!",
  "If you believe hard enough!",
  "Do I look like I care? Just kidding it's a yes I love you bro.",
  "Dude it already happened.",
  "All you have to do is try what's stopping you?",
  "I'll bet you a hundred dollars that is not going to happen",
  "Ask Jericho",
  "Ask Carl",
  "Bakit ako tinatanong niyo? May Carl kayo diba?",
  "..."
]

async def get_waifu(type, category):  # Can't make local to a class (being used by class Waifu, class Roleplay, class NSFW)
  url_string = f"https://api.waifu.pics/{type}/{category}"
  async with aiohttp.ClientSession() as session:
    async with session.get(url_string) as r:
      logger.info(f"Waifu.pics: {r.status}") # debug
      if r.status == 200:
        json_data = await r.json()
        waifu = json_data['url']
  
  return waifu

async def get_waifu_im_embed(type, category):  # Can't make local to a class (being used by class Fun and class NSFW)
  type = "False" if type=="sfw" else "True"
  url_string = f"https://api.waifu.im/random/?selected_tags={category}&is_nsfw={type}"

  async with aiohttp.ClientSession() as session:
    async with session.get(url_string) as resp:
      logger.info(f"Waifu.im: {resp.status}")
      json_data = await resp.json()
      if resp.status in {200, 201}:
        #embed = discord.Embed(color=0xffc0cb)
        embed = discord.Embed(color=int(f"0x{json_data['images'][0]['dominant_color'].lstrip('#')}", 0))
        embed.set_image(url=json_data['images'][0]['url'])

        source = json_data['images'][0]['source']

        #print(json_data)

      else:
        error = json_data['message']
        print(error)
  
  return source, embed

class Info(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.process = psutil.Process()

  @commands.command(aliases=['info', 'sourcecode', 'github'])
  async def about(self, ctx):
    """link to documentation & source code on GitHub"""
    # await ctx.send("Source code & documentation: https://github.com/jerichosy/Abet-Discord-bot")

    embed = discord.Embed(title="FUCK CARL", colour=discord.Colour(0xee615b), url="https://cdn.discordapp.com/attachments/731542246951747594/905830644607758416/abet_bot.png", description="Source code & documentation: [GitHub repository](https://github.com/jerichosy/Abet-Discord-bot)")

    embed.set_image(url="https://opengraph.githubassets.com/89c81820967bbd8115fc6a68d55ef62a3964c8caf19e47a321f12d969ac3b6e3/jerichosy/Abet-Discord-bot")
    embed.set_thumbnail(url=bot.user.display_avatar.url)

    main_guild = self.bot.get_guild(867811644322611200)
    owner = main_guild.get_member(self.bot.owner_id)
    embed.set_author(name=str(owner), icon_url=owner.display_avatar.url)
    version = pkg_resources.get_distribution('discord.py').version
    embed.set_footer(text=f"</> with 💖 by KIA and Tre' Industries using Python (discord.py v{version})", icon_url="https://media.discordapp.net/stickers/946824812658065459.png")

    memory_usage = self.process.memory_full_info().uss / 1024**2
    cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
    embed.add_field(name='Process', value=f'{memory_usage:.2f} MiB\n{cpu_usage:.2f}% CPU')

    #embed.add_field(name='Uptime', value=self.get_bot_uptime(brief=True))  # TODO: 2.0 thing

    await ctx.send(embed=embed)


  @commands.command(aliases=['code'])
  async def showcode(self, ctx):
    """Have the bot upload it's own sourcecode here in Discord"""
    await ctx.send(file=discord.File('main.py'))

  @commands.command()
  async def ping(self, ctx):
    """Get the bot's current websocket and API latency"""
    start_time = time.time()
    to_edit = await ctx.send("Testing ping...")
    end_time = time.time()
    await to_edit.edit(content=f"Pong! {round(bot.latency * 1000)}ms | API: {round((end_time - start_time) * 1000)}ms")

class Fun(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  async def get_json_quote(self, url):
    async with aiohttp.ClientSession() as session:
      async with session.get(url) as resp:
        json_data = await resp.json()
    return json_data

  # Don't make this into an embed
  @commands.command(aliases=['fuckcarl'])
  async def carl(self, ctx):
    """Dish Carl"""
    await ctx.send("https://cdn.discordapp.com/attachments/731542246951747594/905830644607758416/abet_bot.png")

  @app_commands.command()
  @app_commands.guilds(discord.Object(id=867811644322611200))
  async def inspire(self, interaction: discord.Interaction):
    """Sends a random inspirational quote"""
    json_data = await self.get_json_quote("https://zenquotes.io/api/random")
    quote = json_data[0]['q'] + " -" + json_data[0]['a']
    await interaction.response.send_message(quote)

  @app_commands.command()
  @app_commands.guilds(discord.Object(id=867811644322611200))
  async def kanye(self, interaction: discord.Interaction):
    """random Kanye West quotes (Kanye as a Service)"""
    json_data = await self.get_json_quote("https://api.kanye.rest/")
    quote = json_data['quote'] + " - Kanye West"
    await interaction.response.send_message(quote)

  @app_commands.command()
  @app_commands.guilds(discord.Object(id=867811644322611200))
  async def trump(self, interaction: discord.Interaction, in_image_form: Literal['No', 'Yes'] ='No'):
    """random dumbest things Donald Trump has ever said"""
    
    if in_image_form == 'No':
      json_data = await self.get_json_quote("https://api.tronalddump.io/random/quote")
      quote = json_data['value'] + " - Donald Trump"
      await interaction.response.send_message(quote, suppress_embeds=True)
    else:
      async with aiohttp.ClientSession() as session:
        async with session.get('https://api.tronalddump.io/random/meme') as r:
          data = io.BytesIO(await r.read())
          await interaction.response.send_message(file=discord.File(data, "tronalddump.jpg"))

  @commands.command(aliases=['meow'])
  async def cat(self, ctx):
    """Sends a random cat image"""
    async with aiohttp.ClientSession() as session:
      async with session.get('http://aws.random.cat/meow') as r:
        if r.status == 200:
          js = await r.json()
          await ctx.send(js['file'])

  # Lifted from https://github.com/Rapptz/discord.py/blob/master/examples/guessing_game.py
  @commands.command(aliases=['game'])
  async def guess(self, ctx):
    await ctx.send('Guess a number between 1 and 10.')

    def is_correct(m):
      return m.author == ctx.author and m.content.isdigit()

    answer = random.randint(1, 10)

    try:
      guess = await bot.wait_for('message', check=is_correct, timeout=5.0)
    except asyncio.TimeoutError:
      return await ctx.send(f'Sorry, you took too long it was {answer}.')

    if int(guess.content) == answer:
      await ctx.send('You are right!')
    else:
      await ctx.send(f'Oops. It is actually {answer}.')

  # This is so dumb and annoying (thanks to Daniel and Jehu)
  @commands.command()
  @commands.is_owner()
  async def annoy(self, ctx, amount: int, interval_in_minutes: int):
    for _ in range(amount):
      await ctx.send("@everyone", delete_after=2)  # delete after 2 sec
      await asyncio.sleep(interval_in_minutes*60)

  # @app_commands.command()
  # @app_commands.guilds(discord.Object(id=867811644322611200))
  # async def fruits(self, interaction: discord.Interaction, fruits: str):
  #   """This is a test of the autocomplete API"""
  #   await interaction.response.send_message(f'Your favourite fruit seems to be {fruits}')

  # @fruits.autocomplete('fruits')
  # async def fruits_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
  #   fruits = ['Banana', 'Pineapple', 'Apple', 'Watermelon', 'Melon', 'Cherry']
  #   #print(waifu_im_tags)
  #   return [app_commands.Choice(name=fruit, value=fruit) for fruit in fruits if current.lower() in fruit.lower()]

  @app_commands.command()
  @app_commands.guilds(discord.Object(id=867811644322611200))
  @app_commands.describe(is_ephemeral='If "Yes", the image will only be visible to you')
  async def waifu(
    self, 
    interaction: discord.Interaction, 
    tag: str,
    type: Literal['sfw', 'nsfw'] = 'sfw',
    is_ephemeral: Literal['No', 'Yes'] ='No'
  ) -> None:
    """random Waifu images"""
    if type == 'nsfw' and not interaction.channel.is_nsfw() and is_ephemeral == 'No':
      return await interaction.response.send_message("You requested a visible NSFW image in a non-NSFW channel! Please use in the appropriate channel(s).", ephemeral=True)

    #print(waifu_im_tags)

    text, embed = await get_waifu_im_embed(type, tag)
    await interaction.response.send_message(content=text, embed=embed, ephemeral=True if is_ephemeral == 'Yes' else False)

  @waifu.autocomplete('tag')
  async def waifu_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    return [
      app_commands.Choice(name=waifu_im_tag, value=waifu_im_tag) 
      for waifu_im_tag in waifu_im_tags if current.lower() in waifu_im_tag.lower()
    ]

class Waifu(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  async def waifu(self, ctx):  # Note: Despite the same name with the slash cmd, they are not functionally equivalent.
    await ctx.send(await get_waifu("sfw", "waifu"))

  @commands.command()
  async def neko(self, ctx):
    await ctx.send(await get_waifu("sfw", "neko"))

  @commands.command()
  async def shinobu(self, ctx):
    await ctx.send(await get_waifu("sfw", "shinobu"))

  @commands.command()
  async def megumin(self, ctx):
    await ctx.send(await get_waifu("sfw", "megumin"))

  @commands.command()
  async def bully(self, ctx):
    await ctx.send(await get_waifu("sfw", "bully"))

  @commands.command()
  async def cry(self, ctx):
    await ctx.send(await get_waifu("sfw", "cry"))

  @commands.command()
  async def awoo(self, ctx):
    await ctx.send(await get_waifu("sfw", "awoo"))

  @commands.command()
  async def smug(self, ctx):
    await ctx.send(await get_waifu("sfw", "smug"))

  @commands.command()
  async def blush(self, ctx):
    await ctx.send(await get_waifu("sfw", "blush"))

  @commands.command()
  async def smile(self, ctx):
    await ctx.send(await get_waifu("sfw", "smile"))

  @commands.command()
  async def nom(self, ctx):
    await ctx.send(await get_waifu("sfw", "nom"))

  @commands.command()
  async def happy(self, ctx):
    await ctx.send(await get_waifu("sfw", "happy"))

  @commands.command()
  async def dance(self, ctx):
    await ctx.send(await get_waifu("sfw", "dance"))

  @commands.command()
  async def cringe(self, ctx):
    await ctx.send(await get_waifu("sfw", "cringe"))

class Roleplay(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  async def get_roleplay_embed(self, ctx, user_mentioned, type, category, action):
    title = f"{ctx.author.name} {action} "
    if user_mentioned is not None:  # PEP 8
      name = str(user_mentioned)
      size = len(name)
      title += name[:size-5]
    embed = discord.Embed(title=title, color=0xee615b)
    embed.set_image(url=await get_waifu(type, category))
    return embed

  @commands.command()
  async def cuddle(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await self.get_roleplay_embed(ctx, user_mentioned, "sfw", "cuddle", "cuddles"))

  @commands.command()
  async def hug(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await self.get_roleplay_embed(ctx, user_mentioned, "sfw", "hug", "hugs"))

  @commands.command()
  async def kiss(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await self.get_roleplay_embed(ctx, user_mentioned, "sfw", "kiss", "kisses"))

  @commands.command()
  async def lick(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await self.get_roleplay_embed(ctx, user_mentioned, "sfw", "lick", "licks"))

  @commands.command()
  async def pat(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await self.get_roleplay_embed(ctx, user_mentioned, "sfw", "pat", "pats"))

  @commands.command()
  async def bonk(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await self.get_roleplay_embed(ctx, user_mentioned, "sfw", "bonk", "bonks"))

  @commands.command()
  async def yeet(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await self.get_roleplay_embed(ctx, user_mentioned, "sfw", "yeet", "yeets"))

  @commands.command()
  async def wave(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await self.get_roleplay_embed(ctx, user_mentioned, "sfw", "wave", "waves"))

  @commands.command()
  async def highfive(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await self.get_roleplay_embed(ctx, user_mentioned, "sfw", "highfive", "highfives"))

  @commands.command()
  async def handhold(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await self.get_roleplay_embed(ctx, user_mentioned, "sfw", "handhold", "handholds"))

  @commands.command()
  async def bite(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await self.get_roleplay_embed(ctx, user_mentioned, "sfw", "bite", "bites"))

  @commands.command()
  async def glomp(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await self.get_roleplay_embed(ctx, user_mentioned, "sfw", "glomp", "glomps"))

  @commands.command()
  async def slap(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await self.get_roleplay_embed(ctx, user_mentioned, "sfw", "slap", "slaps"))

  # Add kill Abet bot easter egg (go offline then back on and send some scary/taunting shit)
  @commands.command()
  async def kill(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await self.get_roleplay_embed(ctx, user_mentioned, "sfw", "kill", "kills"))

  @commands.command()
  async def kick(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await self.get_roleplay_embed(ctx, user_mentioned, "sfw", "kick", "kicks"))

  @commands.command()
  async def wink(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await self.get_roleplay_embed(ctx, user_mentioned, "sfw", "wink", "winks at"))

  @commands.command()
  async def poke(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await self.get_roleplay_embed(ctx, user_mentioned, "sfw", "poke", "pokes"))

# --- NSFW Start ---
class NSFW(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  @commands.is_nsfw()
  async def hentai(self, ctx):
    """( ͡° ͜ʖ ͡°)"""
    await ctx.send(await get_waifu("nsfw", "waifu"))

  @commands.command()
  @commands.is_nsfw()
  async def nekonsfw(self, ctx):
    await ctx.send(await get_waifu("nsfw", "neko"))

  @commands.command()
  @commands.is_nsfw()
  async def trap(self, ctx):
    await ctx.send(await get_waifu("nsfw", "trap"))

  @commands.command()
  @commands.is_nsfw()
  async def blowjob(self, ctx):
    await ctx.send(await get_waifu("nsfw", "blowjob"))

  @commands.command()
  @commands.is_nsfw()
  async def ass(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "ass")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def ero(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "ero")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def hentai2(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "hentai")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def milf(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "milf")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def oral(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "oral")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def paizuri(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "paizuri")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def ecchi(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "ecchi")
    await ctx.send(text, embed=embed)

# --- NSFW End ---

class Tools(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    self.characters = [
      "Fischl Xiangling",
      "Beidou Noelle",
      "Ningguang Xingqiu",
      "Razor Amber",
      "Bennett Lisa",
      "Barbara Kaeya"
    ]

  def coin_flip(self):
    population = ['Heads', 'Tails']
    weight = [0.1, 0.9]
    return str(choices(population, weight)).strip('[\']')

  @commands.command()
  async def abet(self, ctx, has_question=None):
    """customized Magic 8-Ball"""
    if has_question is None:  # PEP 8
      await ctx.send("What?")
    else:
      await ctx.send(random.choice(abet_response))

  @commands.command()
  async def choose(self, ctx, *, choices):
    """Returns a random choice from the given words/phrases"""
    #choose_phrases = ctx.message.content[8:].split(", ")  # improper way
    choose_phrases = choices.split(", ")  # Split returns a list (square brackets)
    await ctx.send(random.choice(choose_phrases))

  @app_commands.command()
  @app_commands.guilds(discord.Object(id=867811644322611200))  
  async def coinflip(self, interaction: discord.Interaction):
    """Flip a sussy coin"""
    await interaction.response.send_message(self.coin_flip())

  @app_commands.command()
  @app_commands.guilds(discord.Object(id=867811644322611200))
  @app_commands.describe(amount='The amount of sussy coins to flip')
  async def coinfliptally(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 10000]):
    """Flip multiple sussy coins at once!"""
    heads_count = 0
    tails_count = 0
    response = ""

    for _ in range(amount):
      if self.coin_flip() == 'Heads':
        heads_count += 1
      else:
        tails_count += 1

    response += f"Heads: {heads_count}\nTails: {tails_count}"
    await interaction.response.send_message(response)

  # Note to self: Don't send msg in a coding block to retain markdown support
  # TODO: Strictly speaking, the shop resets at 4 AM so this can mislead someone. Also, the bot is in NYC. I'll work on it when it seems needed.
  # TODO: Convert to embed?
  @commands.command(aliases=["paimonsbargains", "paimon'sbargains", "viewshop"])
  async def paimonbargains(self, ctx):
    """Views current Paimon's Bargains items for the month"""
    current_month = datetime.now().month

    def display_future():
      built = "\n\n**Future:**\n"
      for x in range(1, 7):
        built += self.months[((current_month + x) % 12) - 1] + " | " + self.characters[((current_month + x) % 6) - 1] + "\n"

      return built;

    def determine_weapon_series():
      return "\n  Blackcliff series" if current_month % 2 else "\n  Royal series"

    await ctx.send(
      "**Current:**\n"
      + self.months[current_month - 1] + " | " + self.characters[(current_month % 6) - 1]
      + determine_weapon_series()
      + display_future()
    )

  @commands.command(aliases=['wait', 'anime'])
  async def whatanime(self, ctx, url=None):
    """What Anime Is This"""

    if url is None and len(ctx.message.attachments) == 0:
      await ctx.send("Please attach an image / provide a link or URL")
      return

    if url is None:
      url = ctx.message.attachments[0].url
    
    async with ctx.typing():
      response = requests.get(f"https://api.trace.moe/search?cutBorders&url={url}", timeout=7)
      #response = requests.get(f"https://api.trace.moe/search?anilistInfo&url={url}", timeout=7)
      logger.info(f"Trace.moe: {response}") # debug
      json_data = json.loads(response.text)

      reason = ""
      if json_data['error']:
        reason = json_data['error']
      else:  
        file_name = json_data['result'][0]['filename']
        timestamp = ""
        if json_data['result'][0]['episode'] is not None:
          timestamp = f"Episode {json_data['result'][0]['episode']} | "
        timestamp += str(timedelta(seconds=int(json_data['result'][0]['from'])))
        similarity = json_data['result'][0]['similarity']
        video_url = json_data['result'][0]['video']

        anilist_id = json_data['result'][0]['anilist']

        # Even though we can let Trace.moe API handle contacting AniList GraphQL API on our behalf, we will keep the ff. implementation for future reference:
        query = '''
        query ($id: Int) { # Define which variables will be used in the query (id)
          Media (id: $id, type: ANIME) { # Insert our variables into the query arguments (id) (type: ANIME is hard-coded in the query)
            id
            title {
              romaji
              english
              native
            }
            isAdult
          }
        }
        '''

        variables = {
            'id': anilist_id
        }

        response = requests.post("https://graphql.anilist.co/", json={'query': query, 'variables': variables})
        logger.info(f"  AniList GraphQL API: {response}") # debug
        json_data = json.loads(response.text)

        native = "" if json_data['data']['Media']['title']['native'] is None else f"**{json_data['data']['Media']['title']['native']}**\n"
        romaji = "" if json_data['data']['Media']['title']['romaji'] is None else f"**{json_data['data']['Media']['title']['romaji']}**\n"
        english = "" if json_data['data']['Media']['title']['english'] is None else f"**{json_data['data']['Media']['title']['english']}**\n"

    if reason:
      await ctx.send(reason, suppress_embeds=True)
    else:
      await ctx.send(f"<@{ctx.author.id}>\n\n{native}{romaji}{english}``{file_name}``\n{timestamp}\n{'{:.1f}'.format(similarity * 100)}% similarity")

      if json_data['data']['Media']['isAdult']:
        preview_file_name = "SPOILER_preview.mp4"
        warning = "[NSFW]"
      else:
        preview_file_name = "preview.mp4"
        warning = ""

      async with aiohttp.ClientSession() as session:
        async with session.get(video_url) as resp:
          if resp.status != 200:
            return await ctx.send('Could not download preview...')
          data = io.BytesIO(await resp.read())
          await ctx.send(warning, file=discord.File(data, preview_file_name))

  @commands.command(aliases=['sauce', 'source', 'getsource', 'artsource', 'getartsource'])
  async def saucenao(self, ctx, url=None):
    """SauceNao"""

    if url is None and len(ctx.message.attachments) == 0:
      await ctx.send("Please attach an image / provide a link or URL")
      return

    if url is None:
      url = ctx.message.attachments[0].url
    
    async with ctx.typing():
      token = os.getenv("SAUCENAO_TOKEN")
      async with aiohttp.ClientSession() as session:
        async with session.get(f"https://saucenao.com/search.php?db=999&output_type=2&numres=1&url={url}&api_key={token}") as r:
          logger.info(f"SauceNao: {r.status}")
          json_data = await r.json()
          #print(json_data)

          # error checking
          if r.status != 200 or json_data['header']['status'] != 0:
            if json_data['header']['status'] < 0:
              if json_data['header']['status'] == -2:
                return await ctx.send("Search Rate Too High. Your IP has exceeded the basic account type's rate limit of 6 searches every 30 seconds.")
              else:
                return await ctx.send("Client side error (bad image, out of searches, etc)")
            else:
              return await ctx.send("Server side error (failed descriptor gen, failed query, etc). Please try again!")
          
          # if successful
          def get_json_field(prefix, parameter):
            try:
              field = "" if not json_data['results'][0]['data'][parameter] else f"{prefix}{json_data['results'][0]['data'][parameter]}\n"
              #print(json_data['results'][0]['data'][parameter])
            except KeyError:
              field = ""

            return field

          #source = f"**Sauce:** {json_data['results'][0]['data']['source']}\n"
          source = get_json_field("**Sauce:** ", 'source')
          if source == "":
            source = f"**Sauce:** {json_data['results'][0]['data']['ext_urls'][0]}\n"
          # to handle stuff like 
          # https://i.pximg.net/img-original/img/2021/07/28/07/50/29/91550773 with https://cdn.discordapp.com/attachments/870095545992101958/947297823945293834/lASQNdS.jpg or
          # http://i2.pixiv.net/img-original/img/2016/01/16/01/19/56/54734137 with https://cdn.discordapp.com/attachments/870095545992101958/947296081354588211/54734137_p0_master1200.png
          elif "/img-original/img/" in source:
            source = f"**Sauce:** https://pixiv.net/en/artworks/{source[len(source) - 9 : len(source)]}"
          part = get_json_field("**Part:** ", 'part')
          characters = get_json_field("**Character(s):** ", 'characters')
          #characters = "" if json_data['results'][0]['data']['characters'] is None else f"**Character(s):** {json_data['results'][0]['data']['characters']}\n"
          similarity = f"**Similarity:** {float(json_data['results'][0]['header']['similarity'])}%"

          #danbooru = "" if json_data['results'][0]['data']['danbooru_id'] is None else f"Danbooru ID: {json_data['results'][0]['data']['danbooru_id']}\n"
          danbooru = get_json_field("Danbooru ID: ", 'danbooru_id')
          #yandere = "" if json_data['results'][0]['data']['yandere_id'] is None else f"Yandere ID: {json_data['results'][0]['data']['yandere_id']}\n"
          yandere = get_json_field("Yandere ID: ", 'yandere_id')
          #gelbooru = "" if json_data['results'][0]['data']['gelbooru_id'] is None else f"Gelbooru ID: {json_data['results'][0]['data']['gelbooru_id']}\n"
          gelbooru = get_json_field("Gelbooru ID: ", 'gelbooru_id')

          separator = "" if danbooru == "" and yandere == "" and gelbooru == "" else "\n--------------------------\n"

          await ctx.send(f"<@{ctx.author.id}> Note: For anime, use &whatanime\n\n{source}{part}{characters}{similarity}{separator}{danbooru}{yandere}{gelbooru}")

  @commands.command()
  async def weather(self, ctx, location=None):
    if location is None:
      location = ""
    async with ctx.typing():
      async with aiohttp.ClientSession() as session:
        async with session.get(f"https://wttr.in/{location}?0T") as resp:
          logger.info(f"wttr.in response: {resp.status}")
          if await resp.text() == "" or await resp.text() == "Follow @igor_chubin for wttr.in updates":
            return await ctx.send("The weather service is having problems. Please try again later.")
          await ctx.send(f"```{await resp.text()}```")

  @commands.command()
  async def metar(self, ctx, airport_code):
    token = os.getenv("METAR_TOKEN")
    async with ctx.typing():
      async with aiohttp.ClientSession(headers={"Authorization": "BEARER " + token}) as session:
        async with session.get(f"https://avwx.rest/api/metar/{airport_code}") as response:
          logger.info(f"AVWX response: {response.status}")
          json_data = await response.json()
          if response.status != 200:
            return await ctx.send(json_data['error'])
          await ctx.send(json_data['raw'])
        
  @commands.command(aliases=['genshin_character_stats', 'genshincharacters', 'genshincharacter', 'genshin_characters', 'genshin_character', 'character_stats', 'character_stat', 'characterstats', 'characterstat', 'genshin', 'genshininfo'])
  async def genshincharacterstats(self, ctx, uid):
    gs.set_cookie(ltuid = os.getenv("LTUID"), ltoken = os.getenv("LTOKEN"))
    async with ctx.typing():
      data = gs.get_characters(uid)
      data.sort(key=lambda x: (x["rarity"], x["level"]), reverse=True)

      def tally_artifacts(artifact):
        if not artifact:
          return ""

        artifact_list = []
        for x in artifact:
          artifact_list.append(x['set']['name'])

        artifact_count = Counter(artifact_list)
        built2 = ""
        for artifact_set in artifact_count:
          built2 += f", {artifact_count[artifact_set]}pc. {artifact_set}" if artifact_count[artifact_set] >= 2 else ""  # This is okay if it reports a "3pc." or "5pc.". It's kinda funny and provokes envy as well!

        return f"\n    {built2[2:]}" if built2[2:] is not None else "(No 2pc. of any set)"  # TODO: Latter is not tested

      #print(json.dumps(data))

      built = f"{uid}\n"
      for char in data:
        built += f"{char['name']} ({char['rarity']}* {char['element']}): lvl {char['level']} C{char['constellation']} | {char['weapon']['name']} ({char['weapon']['rarity']}* {char['weapon']['type']}): lvl {char['weapon']['level']} R{char['weapon']['refinement']} {tally_artifacts(char['artifacts'])}\n"
      await ctx.reply(f"```{built}```")

  @commands.command(aliases=['resinreplenish', 'replenish', 'resins', 'resinsreplenish', 'replenishment', 'resinreplenishment', 'resinsreplenishment', 'resinfinish', 'resinfinished', 'resinsfinish', 'resinsfinished'])
  async def resin(self, ctx, current_resin: int):
    if current_resin > 160 or current_resin < 0:
      return await ctx.send("❌ Inputted resin must be between 0-160.")

    time_to_fully_replenished = (160 - current_resin) * (8 * 60)
    current_time = time.time()
    finished_time = current_time + time_to_fully_replenished
    await ctx.reply(f"Resin will be fully replenished at: <t:{int(finished_time)}:F> (<t:{int(finished_time)}:R>)")

class Admin(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command(aliases=['delete'])
  @has_permissions(manage_messages=True)
  async def purge(self, ctx, amount: int):
    await ctx.channel.purge(limit=amount+1)

  @commands.command(aliases=['close', 'shutup', 'logoff', 'stop'])
  @has_permissions(administrator=True)  # Retain cause we usually just give alt the Administrator perm or none at all
  async def shutdown(self, ctx):
    await ctx.send("🛑 Shutting down!")
    await bot.close()

  @app_commands.command()
  @app_commands.guilds(discord.Object(id=867811644322611200))
  #@has_permissions(manage_guild=True)
  async def changestatus(self, interaction: discord.Interaction, activity: Literal['Playing', 'Listening to', 'Watching'], status_msg: str):
    """Change the status/activity of the bot"""
    # https://discordpy.readthedocs.io/en/master/api.html#discord.ActivityType

    if activity == 'Playing':
      await bot.change_presence(activity=discord.Game(name=status_msg))
    elif activity == 'Listening to':
      await bot.change_presence(activity=discord.Activity(name=status_msg, type=discord.ActivityType.listening))
    elif activity == 'Watching':
      await bot.change_presence(activity=discord.Activity(name=status_msg, type=discord.ActivityType.watching))

    await interaction.response.send_message(f'✅ My status is now "**{activity} {status_msg}**"')


  @commands.command()
  async def sendmsg(self, ctx, channel_id: int, *, content):
    #print(content)
    channel = bot.get_channel(channel_id)
    await channel.send(content)
    await ctx.send(f"**Sent:** {content}\n**Where:** <#{channel_id}>")

  @commands.command()
  async def sendreply(self, ctx, channel_id: int, message_id: int, *, content):
    channel = bot.get_channel(channel_id)
    message = await channel.fetch_message(message_id)
    await message.reply(content)
    await ctx.send(f"**Replied:** {content}\n**Which message:** {message.jump_url}")

  @commands.command()
  @commands.is_owner()
  async def sync(self, ctx: Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~"]] = None) -> None:
    if not guilds:
      if spec == "~":
        fmt = await ctx.bot.tree.sync(guild=ctx.guild)
      else:
        fmt = await ctx.bot.tree.sync()

      await ctx.send(
        f"Synced {len(fmt)} commands {'globally' if spec is None else 'to the current guild.'}"
      )
      return

    assert guilds is not None
    fmt = 0
    for guild in guilds:
      try:
        await ctx.bot.tree.sync(guild=guild)
      except discord.HTTPException:
        pass
      else:
        fmt += 1

    await ctx.send(f"Synced the tree to {fmt}/{len(guilds)} guilds.")


  #@commands.command()
  #async def checksafe(self, ctx):
    #if ctx.message.channel.is_nsfw():
      #await ctx.send("Yes")

    # the ff. doesn't work?
      #raise commands.errors.NSFWChannelRequired


def findWholeWord(w):
  return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

@bot.event
async def on_message(message):
  if message.author == bot.user:
    return

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

  await bot.process_commands(message)

# Command error msg sender
@bot.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.errors.NSFWChannelRequired):
    # Raise exception if NSFW channel setting disabled
    await ctx.send("This is an NSFW command! Please use in the appropriate channel(s).")
  #elif isinstance(error, commands.errors.CommandNotFound):
  #  pass
  else:
    await ctx.send(error)
  # add more?

@bot.event
async def on_presence_update(before, after):
  if not after.bot:
    logger.info(f"{after} | {after == before}")
    logger.info(f"  BEFORE: {before.activity}")
    logger.info(f"  AFTER:  {after.activity}")
    if after.activity is not None:
      if after.activity.name == 'VALORANT' and before.activity is None:  # This invokes from None -> VALORANT, but won't invoke from Spotify, etc. But it's ok
        channel = bot.get_channel(867811644322611202)  #sala 867811644322611202
        await channel.send(f"@here\nIt's a fine {datetime.today().strftime('%A')}. **Ruin it by following {after.mention}'s footsteps and playing {after.activity.name}!** ⚠️")

async def main():
  async with bot:
    await bot.add_cog(Info(bot))
    await bot.add_cog(Fun(bot))
    await bot.add_cog(Waifu(bot))
    await bot.add_cog(Roleplay(bot))
    await bot.add_cog(NSFW(bot))
    await bot.add_cog(Tools(bot))
    await bot.add_cog(Admin(bot))

    await bot.load_extension('jishaku')

    await bot.start(os.getenv('BOT_TOKEN'))

asyncio.run(main())
